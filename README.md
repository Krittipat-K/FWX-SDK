# FWX-SDK

This is an unofficial Python SDK developed by me for trading on the FWX platform. It is not affiliated with or maintained by FWX.

## 📦 Installation

```bash
pip install git+https://github.com/Krittipat-K/FWX-SDK.git
```

## 🏗️ Initialization

```python
from fwx.perp import FWXPerpSDK,get_raw_pyth_data
from web3 import Web3
from fwx.w3 import get_rpc_detail
from fwx.constant import (
    FWX_MEMBERSHIP_ADDRESS_BASE,
    FWX_PERP_CORE_ADDRESS_BASE,
    FWX_PERP_HELPER_ADDRESS_BASE,
    PYTH_ID
)

rpc = "https://1rpc.io/base"  # Replace with your actual RPC URL
w3 = Web3(Web3.HTTPProvider(rpc))
rpc_detail = get_rpc_detail(rpc)

usdc_base_address = rpc_detail.chain_detail.token_details['USDC'].address
btc_base_address = rpc_detail.chain_detail.token_details['BTC'].address
from dotenv import load_dotenv
load_dotenv()
import os
private_key = os.getenv("PRIVATE_KEY", "0x...")  # Replace with your actual private key

sdk = FWXPerpSDK(
    w3=w3,
    rpc_detail=rpc_detail,
    private_key=private_key,
    membership_address=FWX_MEMBERSHIP_ADDRESS_BASE,
    perp_core_address=FWX_PERP_CORE_ADDRESS_BASE,
    helper_address=FWX_PERP_HELPER_ADDRESS_BASE,
    usdc_address=usdc_base_address,
)
```

## 📗 Usage Examples

You can find full working examples in the Jupyter Notebook:

➡️ [examples/examples_usage.ipynb](examples/examples_usage.ipynb)

The following functions are demonstrated:
- `get_nft_id`
- `get_perp_balance`
- `get_all_positions`
- `deposit_collateral_in_wei`
- `deposit_collateral`
- `get_max_contract_size`
- `open_position_given_contract_size_in_wei`
- `get_contract_size_given_volumn`
- `open_position_given_contract_size`
- `open_position_given_volumn`
- `close_position_with_pos_id`

## 📉 Close a Position

```python
raw_pyth_data = get_raw_pyth_data([PYTH_ID['BTC'],PYTH_ID['USDC']])
sdk.close_position_with_pos_id(
    raw_pyth_data=raw_pyth_data,
    nft_id=sdk.nft_id,
    pos_id=3,
    closing_size=500_000_000_000_000_000,
)
```

## 🧪 Oracle Helper

```python

raw_pyth_data = get_raw_pyth_data([PYTH_ID['BTC'],PYTH_ID['USDC']])
contract_size = sdk.get_contract_size_given_volumn(
    volume=100,
    underlying_symbol="BTC",
    raw_pyth_data=raw_pyth_data
)
contract_size
```

## 📚 Project Structure

```
FWX-SDK/
├── fwx/                  # SDK source code
├── examples_usage.ipynb  # Jupyter notebooks / usage samples
├── README.md             # Documentation
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Build configuration
```

## 🔒 License

MIT License

## 🌐 Links

- [GitHub](https://github.com/Krittipat-K/FWX-SDK)
- Author: Krittipat Krittakom (<Krittipat.kr@ku.th>)
