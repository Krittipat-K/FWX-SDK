from typing import (
    Any,
    List,
    Dict,
    Tuple,
    Optional
)
from web3 import Web3
from web3._utils.contracts import (
    prepare_transaction,
)
from eth_utils.abi import (
    abi_to_signature,
)
from eth_typing import (
    ChecksumAddress,
)
from web3.contract.contract import (
    ContractFunction,
    ContractEvent
)

from web3.types import (
    TxParams,
    BlockIdentifier,
    Wei
)
from web3.types import (
    EventData,
)

from fwx.types import (
    RPCDetail,
    ERC20TransferEventData,
    ERC20TransferArgs,
    FWXPerpCoreGetPositionRespond,
    FWXPerpCoreOpenPositionEventData,
    FWXPerpCoreOpenPositionArgs,
    FWXPerpCoreClosePositionEventData,
    FWXPerpCoreClosePositionArgs,
    FWXPerpHelperGetBalanceRespond,
    FWXPerpHelperGetAllPositionRespond
)
from fwx.w3 import (
    Web3HTTP,
)
from fwx.constant import (
    FWX_MEMBERSHIP_ABI,
    FWX_PERP_CORE_ABI,
    FWX_PERP_HELPER_ABI,
    ERC20_ABI,
)

class BaseContract(Web3HTTP):
    
    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address:ChecksumAddress,
                 abi: List[Dict[str, Any]]
                 ) -> None:
        super().__init__(w3, rpc_detail)
        self.address = contract_address
        self.contract = self.load_contract(abi,self.address)
        
    def get_func_data(self,
                      func:ContractFunction,)->TxParams:
        abi_element_identifier = abi_to_signature(func.abi)
        return prepare_transaction(self.address,
                                   self.w3,
                                   abi_element_identifier,
                                   self.contract.abi,
                                   func.abi,
                                   *func.args or (),
                                   **func.kwargs or {})
        
class ERC20ContractBase(BaseContract):
    
    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address: ChecksumAddress,
                 abi: List[Dict[str, Any]] = ERC20_ABI
                 ) -> None:
        super().__init__(w3, rpc_detail, contract_address, abi)
        
    def balanceOf(self,address:ChecksumAddress) -> ContractFunction:
        
        return self.contract.functions.balanceOf(address)
    
    def allowance(self,owner:ChecksumAddress,spender:ChecksumAddress) -> ContractFunction:
        
        return self.contract.functions.allowance(owner,spender)
    
    def name(self) -> ContractFunction:
        
        return self.contract.functions.name()
    
    def totalSupply(self) -> ContractFunction:
        
        return self.contract.functions.totalSupply()
    
    def symbol(self) -> ContractFunction:
        
        return self.contract.functions.symbol()
    
    def decimals(self) -> ContractFunction:
        
        return self.contract.functions.decimals()
    
    # Transaction Section
    
    def approve(self,spender:ChecksumAddress,amount:int) -> ContractFunction:
        
        return self.contract.functions.approve(spender,amount)
    
    def transfer(self,to:ChecksumAddress,amount:int) -> ContractFunction:
        
        return self.contract.functions.transfer(to,amount)
    
    def transferFrom(self,from_address:ChecksumAddress,to:ChecksumAddress,amount:int) -> ContractFunction:
        
        return self.contract.functions.transferFrom(from_address,to,amount)
    
    def eventTransfer(self) -> ContractEvent:
        
        return self.contract.events.Transfer()
    
class ERC20Contract(ERC20ContractBase):
    
    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address: ChecksumAddress
                 ) -> None:
        super().__init__(w3, rpc_detail, contract_address)
        try:
            self.token_symbol = rpc_detail.chain_detail.address_map[self.address]
            self.decimal = rpc_detail.chain_detail.token_details[self.token_symbol].decimal
            self.unit_type = rpc_detail.chain_detail.token_details[self.token_symbol].unit_type
            self.created_block = rpc_detail.chain_detail.token_details[self.token_symbol].created_block
        except:
            self.token_symbol = self.symbol().call()
            self.decimal = self.decimals().call()
            if self.decimal == 18:
                self.unit_type = 'ether'
            elif self.decimal == 9:
                self.unit_type = 'gwei'
            else:
                raise ValueError('Decimal is not 9 or 18')
            self.created_block = 0
        
    def process_transfer_event_log(self,event_log:EventData) -> ERC20TransferEventData:
        
        base_event_data,arg = self.process_event_data(event_log)
        sender = Web3.to_checksum_address(arg['from'])
        receiver = Web3.to_checksum_address(arg['to'])
        value = int(arg['value'])
        transfer_args = ERC20TransferArgs(sender,receiver,value)
        return ERC20TransferEventData(address=base_event_data.address,
                                       block_hash=base_event_data.block_hash,
                                       block_number=base_event_data.block_number,
                                       transaction_hash=base_event_data.transaction_hash,
                                       log_index=base_event_data.log_index,
                                       transaction_index=base_event_data.transaction_index,
                                       args=transfer_args)
    
    def get_balance_of(self,address:ChecksumAddress,block_identifier:BlockIdentifier='latest') -> Wei:
        
        return self.balanceOf(address).call(block_identifier=block_identifier)
    
    def get_balance_of_with_label(self,address:ChecksumAddress,block_identifier:BlockIdentifier='latest') -> Tuple[ChecksumAddress,Wei]:
        
        return address,self.get_balance_of(address,block_identifier)
    
    def get_allowance(self,owner:ChecksumAddress,spender:ChecksumAddress,block_identifier:BlockIdentifier='latest') -> Wei:
        
        return self.allowance(owner,spender).call(block_identifier=block_identifier)
        
class FWXMembershipContractBase(BaseContract):
    
    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address: ChecksumAddress,
                 abi: List[Dict[str, Any]] = FWX_MEMBERSHIP_ABI
                 ) -> None:
        super().__init__(w3, rpc_detail, contract_address, abi)
        
    def getDefaultMembership(self,
                             wallet_address: ChecksumAddress) -> ContractFunction:
        return self.contract.functions.getDefaultMembership(wallet_address)
    
    def mint(self,
             referral_id: int) -> ContractFunction:
        return self.contract.functions.mint(referral_id)
    
class FWXMembershipContract(FWXMembershipContractBase):
    
    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address: ChecksumAddress
                 ) -> None:
        super().__init__(w3, rpc_detail, contract_address)
        self.w3 = w3
        
    def get_default_membership(self,
                             wallet_address: ChecksumAddress) -> int:
        return self.getDefaultMembership(wallet_address).call()
    
    def mint(self,
             referral_id: int) -> ContractFunction:
        return super().mint(referral_id)
    
class FWXPerpCoreContractBase(BaseContract):

    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address: ChecksumAddress,
                 abi: List[Dict[str, Any]] = FWX_PERP_CORE_ABI
                 ) -> None:
        super().__init__(w3, rpc_detail, contract_address,abi)
        
    def getPosition(self,
                    nft_id:int,
                    underlying_address:ChecksumAddress)->ContractFunction:
        
        return self.contract.functions.getPosition(nft_id,underlying_address)
    
    # Transaction Section
    def depositCollateral(self,
                          nft_id:int,
                          collateral_address:ChecksumAddress,
                          underlying_address:ChecksumAddress,
                          amount:int)->ContractFunction:
        
        return self.contract.functions.depositCollateral(nft_id,collateral_address,underlying_address,amount)
    
    def withdrawCollateral(self,
                           nft_id:int,
                           collateral_address:ChecksumAddress,
                           underlying_address:ChecksumAddress,
                           amount:int,
                           pyth_update_data:List[bytes])->ContractFunction:
        
        return self.contract.functions.withdrawCollateral(nft_id,collateral_address,underlying_address,amount,pyth_update_data)
    
    def openPosition(self,
                     nft_id:int,
                     is_long:bool,
                     collateral_address:ChecksumAddress,
                     underlying_address:ChecksumAddress,
                     contract_size_in_collateral:int,
                     leverage:int,
                     pyth_update_data:List[bytes])->ContractFunction:
        
        return self.contract.functions.openPosition(nft_id,is_long,collateral_address,underlying_address,contract_size_in_collateral,leverage,pyth_update_data)
    
    def closePosition(self,
                      nft_id:int,
                      position_id:int,
                      closing_size:int,
                      pyth_update_data:List[bytes])->ContractFunction:
        
        return self.contract.functions.closePosition(nft_id,position_id,closing_size,pyth_update_data)
    
    def closeAllPositions(self,
                          nft_id:int,
                          pyth_update_data:List[bytes])->ContractFunction:
        
        return self.contract.functions.closeAllPositions(nft_id,pyth_update_data)
    
    # Event Section
    
    def eventOpenPosition(self) -> ContractEvent:
        
        return self.contract.events.OpenPosition()

    def eventClosePosition(self) -> ContractEvent:
        return self.contract.events.ClosePosition()
    
class FWXPerpCoreContract(FWXPerpCoreContractBase):
    
    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address: ChecksumAddress
                 ) -> None:
        super().__init__(w3, rpc_detail, contract_address)
        self.w3 = w3
        
    def get_position(self,
                    nft_id:int,
                    underlying_address:ChecksumAddress)->FWXPerpCoreGetPositionRespond:
        res = self.getPosition(nft_id,underlying_address).call()
        
        return FWXPerpCoreGetPositionRespond(*res)
    
    def get_process_open_position_event_log(self,
                                            event_log: EventData,) -> FWXPerpCoreOpenPositionEventData:
        
        base_event_data,arg = self.process_event_data(event_log)
        owener = Web3.to_checksum_address(arg['owner'])
        nft_id = int(arg['nftId'])
        position_id = int(arg['posId'])
        entry_price = int(arg['entryPrice'])
        leverage = int(arg['leverage'])
        contract_size = int(arg['contractSize'])
        is_long = arg['isLong']
        pair_bytes = arg['pairByte']
        collateral_swap_amount_locked = int(arg['collateralSwappedAmountLock'])
        router_address = Web3.to_checksum_address(arg['router'])
        
        return FWXPerpCoreOpenPositionEventData(address=base_event_data.address,
                                                block_hash=base_event_data.block_hash,
                                                block_number=base_event_data.block_number,
                                                transaction_hash=base_event_data.transaction_hash,
                                                log_index=base_event_data.log_index,
                                                transaction_index=base_event_data.transaction_index,
                                                args=FWXPerpCoreOpenPositionArgs(owener,nft_id,position_id,entry_price,leverage,contract_size,is_long,pair_bytes,collateral_swap_amount_locked,router_address))
        
    def get_process_close_position_event_log(self,event_log:EventData) -> FWXPerpCoreClosePositionEventData:
        base_event_data,arg = self.process_event_data(event_log)
        owener = Web3.to_checksum_address(arg['owner'])
        nft_id = int(arg['nftId'])
        position_id = int(arg['posId'])
        closing_size = int(arg['closingSize'])
        closing_price = int(arg['closingPrice'])
        pnl = int(arg['pnl'])
        is_long = arg['isLong']
        clooe_all_positions = arg['closeAllPosition']
        pair_bytes = arg['pairByte']
        collateral_swap_amount_unlocked = int(arg['collateralSwappedAmountUnlock'])
        router_address = Web3.to_checksum_address(arg['router'])
        
        return FWXPerpCoreClosePositionEventData(address=base_event_data.address,
                                                block_hash=base_event_data.block_hash,
                                                block_number=base_event_data.block_number,
                                                transaction_hash=base_event_data.transaction_hash,
                                                log_index=base_event_data.log_index,
                                                transaction_index=base_event_data.transaction_index,
                                                args=FWXPerpCoreClosePositionArgs(owener,nft_id,position_id,closing_size,closing_price,pnl,is_long,clooe_all_positions,pair_bytes,collateral_swap_amount_unlocked,router_address))
        
class FWXPerpHelperContractBase(BaseContract):
    
    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address: ChecksumAddress,
                 abi: List[Dict[str, Any]] = FWX_PERP_HELPER_ABI
                 ) -> None:
        super().__init__(w3, rpc_detail, contract_address,abi)
        
    def getMaxContractSize(self,
                           perps_core_address:ChecksumAddress,
                           nft_id:int,
                           underlying_address:ChecksumAddress,
                           is_new_long:bool,
                           leverage:int,
                           safety_factor:int,
                           pyth_data:List[Tuple[bytes,Tuple[int,...],Tuple[int,...]]])->ContractFunction:
        
        return self.contract.functions.getMaxContractSize(perps_core_address,nft_id,underlying_address,is_new_long,leverage,safety_factor,pyth_data)
    
    def getBalance(self,
                   perps_core_address:ChecksumAddress,
                   nft_id:int,
                   pyth_data:List[Tuple[bytes,Tuple[int,...],Tuple[int,...]]])->ContractFunction:
        
        return self.contract.functions.getBalance(perps_core_address,nft_id,pyth_data)
    
    def getAllActivePositions(self,
                              perps_core_address:ChecksumAddress,
                              nft_id:int,
                              pyth_data:List[Tuple[bytes,Tuple[int,...],Tuple[int,...]]])->ContractFunction:
        
        return self.contract.functions.getAllActivePositions(perps_core_address,nft_id,pyth_data)
    
class FWXPerpHelperContract(FWXPerpHelperContractBase):
    
    def __init__(self, 
                 w3: Web3, 
                 rpc_detail: RPCDetail,
                 contract_address: ChecksumAddress
                 ) -> None:
        super().__init__(w3, rpc_detail, contract_address)
        self.w3 = w3
        
    def get_max_contract_size(self,
                              perps_core_address:ChecksumAddress,
                              nft_id:int,
                              underlying_address:ChecksumAddress,
                              is_new_long:bool,
                              leverage:int,
                              safety_factor:int,
                              pyth_data:List[Tuple[bytes,Tuple[int,...],Tuple[int,...]]]) -> Wei:
        
        return self.getMaxContractSize(perps_core_address,nft_id,underlying_address,is_new_long,leverage,safety_factor,pyth_data).call()
    
    def get_balance(self,
                    perps_core_address:ChecksumAddress,
                    nft_id:int,
                    pyth_data:List[Tuple[bytes,Tuple[int,...],Tuple[int,...]]]) -> FWXPerpHelperGetBalanceRespond:
        
        res = self.getBalance(perps_core_address,nft_id,pyth_data).call()
        return FWXPerpHelperGetBalanceRespond(*res)
    
    def get_all_active_positions(self,
                                 perps_core_address:ChecksumAddress,
                                 nft_id:int,
                                 pyth_data:List[Tuple[bytes,Tuple[int,...],Tuple[int,...]]]) -> Optional[List[FWXPerpHelperGetAllPositionRespond]]:
        
        res = self.getAllActivePositions(perps_core_address,nft_id,pyth_data).call()
        result:list[FWXPerpHelperGetAllPositionRespond] = []
        for pos in res:
            if len(pos) > 0:
                result.append(FWXPerpHelperGetAllPositionRespond(*pos))
                
        if len(result) == 0:
            return None
        
        return result