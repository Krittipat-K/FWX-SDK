from typing import (
    NamedTuple, 
    Union,
    Sequence,
    NewType,
    Dict,
    Optional
)
from hexbytes import HexBytes
from eth_typing import (
    Address,
    ChecksumAddress,
    HexStr,
)
from web3.types import (
    Wei,
    Nonce,
)

class AccessListEntry(NamedTuple):
    address: HexStr
    storageKeys: Sequence[HexStr]

AddressLike = Union[Address, ChecksumAddress,str]
AddressLike = Union[Address, ChecksumAddress,str]
AccessList = NewType("AccessList", Sequence[AccessListEntry])

class TokenDetail(NamedTuple):
    symbol: str
    address: ChecksumAddress
    decimal: int
    unit_type: str
    created_block: int
    
class ChainDetail(NamedTuple):
    
    native:str
    wrap_native:str
    wrap_native_address:ChecksumAddress
    token_details:Dict[str,TokenDetail]
    address_map:Dict[ChecksumAddress,str] = {}
    
class RPCDetail(NamedTuple):
    rpc: str
    chain_id: int
    chain_detail: ChainDetail

class TxParamsInput(NamedTuple):
    accessList: Optional[AccessList] = None
    blobVersionedHashes: Optional[Sequence[Union[str, HexStr, bytes, HexBytes]]] = None
    chinId: Optional[int]  = None
    data: Optional[Union[bytes, HexStr] ]= None
    from_address: Optional[ChecksumAddress] = None
    gas: Optional[int] = None
    gasPrice: Optional[Wei] = None
    maxFeePerBlobGas: Optional[Union[str, Wei]] = None
    maxFeePerGas: Optional[Union[str, Wei]] = None
    maxPriorityFeePerGas: Optional[Union[str, Wei]] = None
    nonce: Optional[Nonce] = None
    to: Optional[ChecksumAddress] = None
    type: Optional[Union[int, HexStr]] = None
    value: Optional[Wei] = None
    
class BaseEventData(NamedTuple):
    address: ChecksumAddress
    block_hash: HexBytes
    block_number: int
    event: str
    log_index: int
    transaction_hash: HexBytes
    transaction_index: int
    
class ERC20TransferArgs(NamedTuple):
    from_address: ChecksumAddress
    to_address: ChecksumAddress
    value: int
    
class ERC20TransferEventData(BaseEventData):
    def __new__(cls, address: ChecksumAddress, block_hash: HexBytes, block_number: int, log_index: int, transaction_hash: HexBytes, transaction_index: int, args: ERC20TransferArgs) -> 'ERC20TransferEventData':
        return super().__new__(cls, address, block_hash, block_number, "Transfer", log_index, transaction_hash, transaction_index)
    
    def __init__(self, address: ChecksumAddress, block_hash: HexBytes, block_number: int, log_index: int, transaction_hash: HexBytes, transaction_index: int, args:ERC20TransferArgs) -> None:
        self.args = args
        
class FWXPerpCoreGetPositionRespond(NamedTuple):
    pos_id:int
    last_settle_timestamp:int
    collateral_address:ChecksumAddress
    underlying_address:ChecksumAddress
    entry_price:int
    contract_size:int
    collateral_locked:int
    leverage:int
    
class FWXPerpCoreOpenPositionArgs(NamedTuple):
    owner:ChecksumAddress
    nft_id:int
    pos_id:int
    entry_price:int
    leverage:int
    contract_size:int
    is_long:bool
    pair_bytes32:bytes
    collateral_swap_amount_locked:int
    router_address:ChecksumAddress
    
class FWXPerpCoreOpenPositionEventData(BaseEventData):
    def __new__(cls, address: ChecksumAddress, block_hash: HexBytes, block_number: int, log_index: int, transaction_hash: HexBytes, transaction_index: int, args: FWXPerpCoreOpenPositionArgs) -> 'FWXPerpCoreOpenPositionEventData':
        return super().__new__(cls, address, block_hash, block_number, "OpenPosition", log_index, transaction_hash, transaction_index)
    
    def __init__(self, address: ChecksumAddress, block_hash: HexBytes, block_number: int, log_index: int, transaction_hash: HexBytes, transaction_index: int, args:FWXPerpCoreOpenPositionArgs) -> None:
        self.args = args
    
class FWXPerpCoreClosePositionArgs(NamedTuple):
    owner:ChecksumAddress
    nft_id:int
    pos_id:int
    closing_size:int
    close_price:int
    pnl:int
    is_long:bool
    close_all_position:bool
    pair_bytes32:bytes
    collateral_swap_amount_unlocked:int
    router_address:ChecksumAddress
    
class FWXPerpCoreClosePositionEventData(BaseEventData):
    def __new__(cls, address: ChecksumAddress, block_hash: HexBytes, block_number: int, log_index: int, transaction_hash: HexBytes, transaction_index: int, args: FWXPerpCoreClosePositionArgs) -> 'FWXPerpCoreClosePositionEventData':
        return super().__new__(cls, address, block_hash, block_number, "ClosePosition", log_index, transaction_hash, transaction_index)
    
    def __init__(self, address: ChecksumAddress, block_hash: HexBytes, block_number: int, log_index: int, transaction_hash: HexBytes, transaction_index: int, args:FWXPerpCoreClosePositionArgs) -> None:
        self.args = args
        
class FWXPerpHelperGetBalanceRespond(NamedTuple):
    net_balance:int
    avaliable_balance:int
    
class FWXPerpHelperGetAllPositionRespond(NamedTuple):
    pos_id:int
    is_long:bool
    collateral_address:ChecksumAddress
    underlying_address:ChecksumAddress
    entry_price:int
    current_price:int
    contract_size:int
    collateral_swapped_amount:int
    liquidation_price:int
    pnl:int
    roe:int
    margin:int
    leverage:int
    tp_price:int
    sl_price:int