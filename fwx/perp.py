from web3 import Web3
from web3.types import (
    Wei,
)
from eth_typing import (
    ChecksumAddress,
)
from fwx.types import (
    RPCDetail,
    FWXPerpHelperGetBalanceRespond,
    FWXPerpHelperGetAllPositionRespond
)
from web3.contract.contract import (
    ContractFunction,
)
from fwx.contract import (
    ERC20Contract,
    FWXMembershipContract,
    FWXPerpCoreContract,
    FWXPerpHelperContract
)

from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Optional
)
from fwx.constant import (
    PYTH_ID,
    MAX_UINT
)
from fwx.w3 import (
    Web3HTTPWallet
)
from fwx.types import (
    TxParamsInput
)
from hexbytes import HexBytes
import requests
import logging
logging.basicConfig(level=logging.INFO)

def get_raw_pyth_fwx_data()->Dict[str,Any]:
        url = 'https://hermes-pyth.fwx.finance/?pyth=perp&encoding=hex'
        data = requests.get(url).json()
        return data
    
def get_raw_pyth_data(list_of_pyth_id: List[str])->Dict[str,Any]:
    base_url = 'https://hermes.pyth.network/v2/updates/price/latest'
    endpoint = ''
    for i in range(len(list_of_pyth_id)):
        if i == 0:
            endpoint += f'?ids%5B%5D={list_of_pyth_id[i]}'
        else:
            endpoint += f'&ids%5B%5D={list_of_pyth_id[i]}'
    url = base_url + endpoint
    data = requests.get(url).json()
    return data

def create_pyth_data(raw_pyth_data:Dict[str,Any])->List[Tuple[bytes,Tuple[int, ...],Tuple[int, ...]]]:
    pyth_data:List[Tuple[bytes,Tuple[int, ...],Tuple[int, ...]]] = []
    for i in raw_pyth_data['parsed']:
        
        id:bytes = bytes.fromhex(i['id'])
        price:Tuple[int, ...] = tuple([int(j) for j in i['price'].values()])
        ema_price:Tuple[int, ...] = tuple([int(j) for j in i['ema_price'].values()])
        d:Tuple[bytes, Tuple[int, ...], Tuple[int, ...]] = (id, price, ema_price)
        pyth_data.append(d)
        
    return pyth_data

def create_pyth_update_data(raw_pyth_data:Dict[str,Any])->List[bytes]:

    return [bytes.fromhex(raw_pyth_data['binary']['data'][0])]


class Perp:
    
    def __init__(self,
                 w3:Web3,
                 rpc_detail:RPCDetail,
                 membership_address: str,
                 perp_core_address: str,
                 helper_address: str,
                 usdc_address: str
                 ) -> None:
        self.membership = FWXMembershipContract(w3, rpc_detail, Web3.to_checksum_address(membership_address))
        self.core = FWXPerpCoreContract(w3, rpc_detail, Web3.to_checksum_address(perp_core_address))
        self.helper = FWXPerpHelperContract(w3, rpc_detail, Web3.to_checksum_address(helper_address))
        self.usdc = ERC20Contract(w3, rpc_detail, Web3.to_checksum_address(usdc_address))
        
    def get_perp_balance(self,
                               nft_id:int)->FWXPerpHelperGetBalanceRespond:
        raw_pyth_data = get_raw_pyth_fwx_data()
        pyth_data = create_pyth_data(raw_pyth_data)
        
        return self.helper.get_balance(self.core.address,nft_id,pyth_data)

    def get_all_positions(self,nft_id:int) -> Optional[List[FWXPerpHelperGetAllPositionRespond]]:
        raw_pyth_data = get_raw_pyth_fwx_data()
        pyth_data = create_pyth_data(raw_pyth_data)

        return  self.helper.get_all_active_positions(self.core.address,
                                                                nft_id,
                                                                pyth_data)
        
    def deposit_collateral_in_wei(self,
                                        nft_id:int,
                                        amount:int,
                                        underlying_address:str,)->ContractFunction:
        deposit_func = self.core.depositCollateral(nft_id,self.usdc.address,Web3.to_checksum_address(underlying_address),amount)
        return deposit_func

    def get_max_contract_size(self,
                              nft_id:int,
                              underlying_address:ChecksumAddress,
                              raw_pyth_data:Dict[str,Any],
                              is_new_long:bool,
                              leverage:int,
                              safety_factor:int=980000)->Wei:
        pyth_data = create_pyth_data(raw_pyth_data)
        leverage = leverage*10**18

        return self.helper.get_max_contract_size(self.core.address,
                                                nft_id,
                                                underlying_address,
                                                is_new_long,
                                                leverage,
                                                safety_factor,
                                                pyth_data)
        
    def open_position_given_contract_size_in_wei(self,
                                                       nft_id:int,
                                                       is_long:bool,
                                                       is_new_long:bool,
                                                       contract_size:int,
                                                       leverage:int,
                                                       underlying_address:ChecksumAddress,
                                                       raw_pyth_data:Dict[str,Any])->ContractFunction:
        max_contract_size = self.get_max_contract_size(nft_id,
                                                       underlying_address,
                                                       raw_pyth_data,
                                                       is_new_long,
                                                       leverage)
        logging.info(f"Max contract size: {max_contract_size}")
        if contract_size > max_contract_size:
            contract_size = max_contract_size
            logging.warning("Contract size is too large, setting to max contract size")
        leverage = leverage*10**18
        pyth_updata_data = create_pyth_update_data(raw_pyth_data)
        func = self.core.openPosition(nft_id,
                                      is_long,
                                      self.usdc.address,
                                      Web3.to_checksum_address(underlying_address),
                                      contract_size,
                                      leverage,
                                      pyth_updata_data,
                                      )
        return func
    
    def get_contract_size_given_volumn(self,
                                       volume:float,
                                       underlying_symbol:str,
                                       raw_pyth_data:Dict[str,Any],
                                       )->float:
        contract_size = 0
        for i in raw_pyth_data['parsed']:
            if i['id'] == PYTH_ID[underlying_symbol]:
                price = int(i['price']['price'])*10**i['price']['expo']
                contract_size = volume/price
                break
            
        if contract_size == 0:
            raise ValueError("Invalid underlying symbol")
            
        return contract_size
    
    def close_position_with_pos_id(self,
                                         raw_pyth_data:Dict[str,Any],
                                         nft_id:int,
                                         pos_id:int,
                                         closing_size:int,
                                         )->ContractFunction:
        
        pyth_update_data = create_pyth_update_data(raw_pyth_data)
        func =  self.core.closePosition(nft_id,
                                        pos_id,
                                        closing_size,
                                        pyth_update_data)
        return func
    
class FWXPerpSDK(Web3HTTPWallet):
    def __init__(self,
                 w3:Web3,
                 rpc_detail:RPCDetail,
                 private_key:str,
                 membership_address:str,
                 perp_core_address:str,
                 helper_address:str,
                 usdc_address:str,
                 nft_id:int=0) -> None:
        super().__init__(w3, rpc_detail, private_key)
        self.perp = Perp(self.w3, rpc_detail, membership_address, perp_core_address, helper_address, usdc_address)
        self.nft_id = nft_id

    def get_nft_id(self,referal_id:int)->None:
        self.nft_id =  self.perp.membership.get_default_membership(self.wallet_address)
        if self.nft_id == 0:
            logging.info("Minting NFT ID")
            txn_params = self.create_txn_params(TxParamsInput())
            txn_params =  self.perp.membership.mint(referal_id).build_transaction(txn_params)
            txn =  self.send_transaction(txn_params)
            self.w3.eth.wait_for_transaction_receipt(txn)
            self.nft_id =  self.perp.membership.get_default_membership(self.wallet_address)
            
    def get_perp_balance(self,
                         nft_id:int=0)->FWXPerpHelperGetBalanceRespond:
        if nft_id == 0:
            if self.nft_id == 0:
                raise ValueError("NFT ID is not set. Please call get_nft_id() first.")
            nft_id = self.nft_id
        
        return self.perp.get_perp_balance(nft_id)
    
    def get_all_positions(self,nft_id:int=0) -> Optional[List[FWXPerpHelperGetAllPositionRespond]]:
        
        if nft_id == 0:
            if self.nft_id == 0:
                raise ValueError("NFT ID is not set. Please call get_nft_id() first.")
            nft_id = self.nft_id
        
        return self.perp.get_all_positions(nft_id)
        
    def deposit_collateral_in_wei(self,
                                  amount:int,
                                  underlying_address:str,
                                  tx_params_input:TxParamsInput=TxParamsInput(),
                                  nft_id:int=0)->HexBytes:
        if nft_id == 0:
            if self.nft_id == 0:
                raise ValueError("NFT ID is not set. Please call get_nft_id() first.")
            nft_id = self.nft_id
            
        owner = self.wallet_address
        spender = self.perp.core.address
        allowance:int = int(self.perp.usdc.get_allowance(owner,spender))
        
        if allowance < amount:
            func = self.perp.usdc.approve(spender,MAX_UINT)
            txn_params = self.create_txn_params(TxParamsInput())
            txn_params = func.build_transaction(txn_params)
            txn = self.send_transaction(txn_params)
            self.w3.eth.wait_for_transaction_receipt(txn)
            
        deposit_func = self.perp.deposit_collateral_in_wei(nft_id, amount, underlying_address)
        txn_params = self.create_txn_params(tx_params_input)
        txn_params = deposit_func.build_transaction(txn_params)
        txn = self.send_transaction(txn_params)
        self.w3.eth.wait_for_transaction_receipt(txn)
        return txn
        


    def deposit_collateral(self,
                                 amount:int,
                                 underlying_address:str,
                                 tx_params_input:TxParamsInput=TxParamsInput(),
                                 nft_id:int=0)->HexBytes:
        
        amount_in_wei = Web3.to_wei(amount,'mwei')
        
        return self.deposit_collateral_in_wei(amount_in_wei,
                                              underlying_address,   
                                                tx_params_input,
                                                nft_id)
    
    def get_max_contract_size(self,
                              underlying_address:ChecksumAddress,
                              raw_pyth_data:Dict[str,Any],
                              is_new_long:bool,
                              leverage:int,
                              safety_factor:int=980000,
                              nft_id:int=0)->Wei:
        
        if nft_id == 0:
            if self.nft_id == 0:
                raise ValueError("NFT ID is not set. Please call get_nft_id() first.")
            nft_id = self.nft_id
            
        return self.perp.get_max_contract_size(nft_id,
                                                underlying_address,
                                                raw_pyth_data,
                                                is_new_long,
                                                leverage,
                                                safety_factor)
        
    def open_position_given_contract_size_in_wei(self,
                                                 is_long:bool,
                                                 is_new_long:bool,
                                                 contract_size:int,
                                                 leverage:int,
                                                 underlying_address:ChecksumAddress,
                                                 raw_pyth_data:Dict[str,Any],
                                                 nft_id:int=0,
                                                 tx_params_input:TxParamsInput=TxParamsInput(),
                                                 )->HexBytes:
        if nft_id == 0:
            if self.nft_id == 0:
                raise ValueError("NFT ID is not set. Please call get_nft_id() first.")
            nft_id = self.nft_id
        
        func = self.perp.open_position_given_contract_size_in_wei(nft_id,
                                                                   is_long,
                                                                   is_new_long,
                                                                   contract_size,
                                                                   leverage,
                                                                   underlying_address,
                                                                   raw_pyth_data)
        value = len(raw_pyth_data['parsed']) + len(raw_pyth_data['binary'])
        tx_params_input = tx_params_input._replace(value=Wei(value))
        tx_params = self.create_txn_params(tx_params_input)
        tx_params = func.build_transaction(tx_params)
        txn = self.send_transaction(tx_params)
        self.w3.eth.wait_for_transaction_receipt(txn)
        return txn
        
    def get_contract_size_given_volumn(self,
                                       volume:float,
                                       underlying_symbol:str,
                                       raw_pyth_data:Dict[str,Any],
                                       )->float:
        contract_size = 0
        for i in raw_pyth_data['parsed']:
            if i['id'] == PYTH_ID[underlying_symbol]:
                price = int(i['price']['price'])*10**i['price']['expo']
                contract_size = volume/price
                break
            
        if contract_size == 0:
            raise ValueError("Invalid underlying symbol")
            
        return contract_size
    
    def open_position_given_contract_size(self,
                                          is_long:bool,
                                          contract_size:float,
                                          leverage:int,
                                          underlying_address:ChecksumAddress,
                                          raw_pyth_data:Dict[str,Any],
                                          is_new_long:bool,
                                          tx_params_input:TxParamsInput=TxParamsInput(),
                                          nft_id:int=0)->HexBytes:
        underlying_symbol = self.address_map[underlying_address]
        underlying = self.token_details[underlying_symbol]
        contract_size_in_wei = Web3.to_wei(contract_size,underlying.unit_type)
        
        return self.open_position_given_contract_size_in_wei(is_long,
                                                            is_new_long,
                                                            contract_size_in_wei,
                                                            leverage,
                                                            underlying_address,
                                                            raw_pyth_data,
                                                            nft_id,
                                                            tx_params_input)
        
    def open_position_given_volumn(self,
                                            is_long:bool,
                                            volume:float,
                                            leverage:int,
                                            underlying_address:ChecksumAddress,
                                            raw_pyth_data:Dict[str,Any],
                                            is_new_long:bool,
                                            tx_params_input:TxParamsInput=TxParamsInput(),
                                            nft_id:int=0)->HexBytes:
            contract_size = self.get_contract_size_given_volumn(volume,self.address_map[underlying_address],raw_pyth_data)
            
            return self.open_position_given_contract_size(is_long,
                                                          contract_size,
                                                          leverage,
                                                          underlying_address,
                                                          raw_pyth_data,
                                                          is_new_long,
                                                          tx_params_input,
                                                          nft_id)
        
    def close_position_with_pos_id(self,
                                   raw_pyth_data:Dict[str,Any],
                                   pos_id:int,
                                   closing_size:int,
                                   nft_id:int=0,
                                   tx_params_input:TxParamsInput=TxParamsInput()
                                   )->HexBytes:
        if nft_id == 0:
            if self.nft_id == 0:
                raise ValueError("NFT ID is not set. Please call get_nft_id() first.")
            nft_id = self.nft_id
        funce = self.perp.close_position_with_pos_id(raw_pyth_data,
                                                        nft_id,
                                                        pos_id,
                                                        closing_size)
        
        value = len(raw_pyth_data['parsed']) + len(raw_pyth_data['binary'])
        tx_params_input = tx_params_input._replace(value=Wei(value))
        tx_params = self.create_txn_params(tx_params_input)
        tx_params = funce.build_transaction(tx_params)
        txn = self.send_transaction(tx_params)
        self.w3.eth.wait_for_transaction_receipt(txn)
        return txn