from hexbytes import HexBytes
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from typing import (
    Any,
    Optional,  
    List,
    Tuple,
    Dict)
from eth_typing import (
    ChecksumAddress,
    BlockIdentifier
)
from web3.contract.contract import (
    Contract,
    ContractEvent
)
from web3.types import (
    EventData,
    TxReceipt,
    TxParams,
    Wei,
    Nonce,
)
from web3._utils.events import (
    EventLogErrorFlags,
)
from eth_account.datastructures import (
    SignedTransaction,
)
from eth_account.signers.local import (
    LocalAccount,
)

from fwx.types import (
    TokenDetail,
    ChainDetail,
    RPCDetail,
    TxParamsInput,
    BaseEventData
)
from fwx.constant import (
    CHAIN_DETAILS
)


def get_token_detail(token_symbol:str,
                     chain_id:str)->TokenDetail:
    chain_detail = CHAIN_DETAILS[chain_id]
    try:
        token_detail:dict[str,Any] = chain_detail['token_details'][token_symbol]
    except KeyError:
        raise ValueError(f"Token {token_symbol} not found in chain {chain_id} or not supported")
    
    return TokenDetail(
        symbol = token_detail['symbol'],
        address = Web3.to_checksum_address(token_detail['address']),
        decimal = token_detail['decimal'],
        unit_type = token_detail['unit_type'],
        created_block = token_detail['created_block']
    )
    
def get_chain_detail(chain_id:str)->ChainDetail:
    
    try:
        chain_detail:dict[str,Any] = CHAIN_DETAILS[chain_id]
    except KeyError:
        raise ValueError(f"Chain {chain_id} not found or not supported")
    
    token_details:dict[str,TokenDetail] = {}
    address_map:dict[ChecksumAddress,str] = {}
    for token_symbol,token_detail in chain_detail['token_details'].items():
        token_details[token_symbol] = TokenDetail(
            symbol = token_detail['symbol'],
            address = Web3.to_checksum_address(token_detail['address']),
            decimal = token_detail['decimal'],
            unit_type = token_detail['unit_type'],
            created_block = token_detail['created_block']
        )
        address_map[Web3.to_checksum_address(Web3.to_checksum_address(token_detail['address']))] = token_detail['symbol']
    
    return ChainDetail(
        native = chain_detail['native'],
        wrap_native = chain_detail['wrapNative'],
        wrap_native_address = Web3.to_checksum_address(chain_detail['wrapNativeAddress']),
        token_details = token_details,
        address_map = address_map
    )
    
def get_rpc_detail(rpc:str)->RPCDetail:
    w3 = Web3(Web3.HTTPProvider(rpc))
    chain_id = w3.eth.chain_id
    chain_detail = get_chain_detail(str(chain_id))
    
    return RPCDetail(
        rpc = rpc,
        chain_id = chain_id,
        chain_detail = chain_detail
    )
    
class Web3HTTP:
    def __init__(self,
                 w3:Web3,
                 rpc_detail:RPCDetail) -> None:
        self.w3 = w3
        if rpc_detail.chain_id == 43114:
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0) # type: ignore
            
        self.chain_id = rpc_detail.chain_id
        self.native = rpc_detail.chain_detail.native
        self.wrap_native = rpc_detail.chain_detail.wrap_native
        self.wrap_native_address = rpc_detail.chain_detail.wrap_native_address
        self.token_details = rpc_detail.chain_detail.token_details
        self.address_map = rpc_detail.chain_detail.address_map
        
    def load_contract(self,
                      abi:List[Dict[str, Any]],
                      address:ChecksumAddress) -> Contract:
        return self.w3.eth.contract(abi=abi,address=address)
    
    def process_receipt(self,
                        receipt:TxReceipt,
                        event:ContractEvent,
                        error:EventLogErrorFlags=EventLogErrorFlags.Discard)->Tuple[EventData]:
        
        return event.process_receipt(receipt,errors=error)
    
    def get_event_data_with_txn(self,
                                txn:HexBytes,
                                event:ContractEvent,
                                error:EventLogErrorFlags=EventLogErrorFlags.Discard) -> Tuple[EventData]:
        receipt:TxReceipt = self.w3.eth.get_transaction_receipt(txn)
        if not receipt:
            raise ValueError(f"Transaction {txn.to_0x_hex()} not found")
        return self.process_receipt(receipt, event, error)
    
    def get_event_data_with_block(self,
                                  event:ContractEvent,
                                  argument_filters:Optional[Dict[str, Any]]=None,
                                  from_block:Optional[BlockIdentifier]=None,
                                  to_block:Optional[BlockIdentifier]=None,)-> Tuple[EventData]:
        return event.get_logs(
            argument_filters=argument_filters,
            from_block=from_block,
            to_block=to_block
        )
        
    def get_base_fee(self,
                     block_identifier:BlockIdentifier='pending') -> Wei:
        block_data = self.w3.eth.get_block(block_identifier)
        return block_data.get('baseFeePerGas', Wei(0))
        
    def process_event_data(self, event_data:EventData) -> Tuple[BaseEventData, Dict[str, Any]]:
        address: ChecksumAddress = Web3.to_checksum_address(event_data['address'])
        blockHash: HexBytes = HexBytes(event_data['blockHash'])
        blockNumber: int = int(event_data['blockNumber'])
        logIndex: int = int(event_data['logIndex'])
        transactionHash: HexBytes = HexBytes(event_data['transactionHash'])
        transactionIndex: int = int(event_data['transactionIndex'])
        event_name = event_data['event']
        args = event_data['args']
        return BaseEventData(address,blockHash,blockNumber,event_name,logIndex,transactionHash,transactionIndex),args 
    
class Web3HTTPWallet(Web3HTTP):
    def __init__(self,
                 w3:Web3,
                 rpc_detail:RPCDetail,
                 private_key:str) -> None:
        super().__init__(w3, rpc_detail)
        self.__private_key = private_key
        account:LocalAccount = self.w3.eth.account.from_key(private_key)
        self.wallet_address:ChecksumAddress = account.address
        self.last_nonce:Optional[Nonce] = None
        
    def create_txn_params(self,
                          tx_params_input:TxParamsInput)->TxParams:
        
        txn_params:TxParams = {'from':self.wallet_address,
                               'chainId':self.chain_id}
        
        if 'nonce' not in txn_params:
            if self.last_nonce is None:
                self.last_nonce = Nonce(0)
            nonce:Nonce = max(self.last_nonce,self.w3.eth.get_transaction_count(self.wallet_address))
            txn_params['nonce'] = nonce
            
        for key,value in tx_params_input._asdict().items():
            if value is not None:
                txn_params[key] = value
            
        return txn_params
    
    def checking_txn_params(self,
                                  txn_params:TxParams,
                                  trick:float=1.5,
                                  priority_multipier:float=1) -> TxParams:
        
        if 'to' not in txn_params:
            raise ValueError("Destination address is required")
        
        priority = None
        max_priority_fee = 0
        if 'maxPriorityFeePerGas' not in txn_params:
            priority = self.w3.eth.max_priority_fee
            max_priority_fee = int(priority * priority_multipier)
            txn_params['maxPriorityFeePerGas'] = Wei(max_priority_fee)
        else:
            max_priority_fee = int(txn_params['maxPriorityFeePerGas'])
            
        base_fee = None
        if 'maxFeePerGas' not in txn_params:
            base_fee = self.get_base_fee()
            max_fee_per_gas = int(base_fee * 2 + max_priority_fee)
            txn_params['maxFeePerGas'] = Wei(max_fee_per_gas)
            
        gas = None
        if 'gas' not in txn_params:
            gas = self.w3.eth.estimate_gas(txn_params)
            txn_params['gas'] = Wei(int(gas * trick))
            
        nonce = None
        if 'nonce' not in txn_params:
            if self.last_nonce is None:
                self.last_nonce = Nonce(0)
            nonce = self.w3.eth.get_transaction_count(self.wallet_address)
            txn_params['nonce'] = max(self.last_nonce,nonce)
            
        if 'from' not in txn_params:
            txn_params['from'] = self.wallet_address
            
        if 'chainId' not in txn_params:
            txn_params['chainId'] = self.chain_id
            
        if 'value' not in txn_params:
            txn_params['value'] = Wei(0)
            
        return txn_params
    
    def send_transaction(self,
                         txn_params:TxParams,
                         trick:float=1.5,
                         priority_multipier:float=1) -> HexBytes:
        txn_params = self.checking_txn_params(txn_params, trick, priority_multipier)
        signed_txn:SignedTransaction = self.w3.eth.account.sign_transaction(txn_params,
                                                                            private_key=self.__private_key)
        txn_hash:HexBytes = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        return txn_hash