from brownie import (
    network,
    accounts,
    config,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    MockWETH,
    MockDAI,
    Contract,
)
from web3 import Web3


LOCAL_BLOCKCHAIN_DEVELOPMENT = {"ganche-local", "development", "ganache-cli", "mainnet-fork"}
FORKED_LOCAL_ENVOIRMENT = {"mainnet-fork", "mainnet-fork-dev"}


def get_account(index=None, id=None):
    """
    Return account based on the current active network deploying the contract.
    @para: index - for specific index from brownie accounts list
       id - for pre-loaded brownie accounts
       not provided and not on a testnet - brownie account[0]
       default - from config file based on network
    @return: brownie.accounts[account]
    """
    if index:
        return accounts[index]
    if id:
        return accounts.add[id]
    if network.show_active() in LOCAL_BLOCKCHAIN_DEVELOPMENT or network.show_active() in FORKED_LOCAL_ENVOIRMENT:
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


# contract name to mock mapping
contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "dai_usd_price_feed": MockV3Aggregator,
    "link_token": LinkToken,
    "fau_token": MockDAI,
    "weth_token": MockWETH,
}


def get_contract(contract_name):
    """This function will grab the contract address from brownie config file if defined,
    otherwise, it will deploy a mock version of that contract and will return that
    contract.

        Args:
            contract_name (string)

        Returns:
            brownie.network.contract.ProjectNetwork - the most recently deployed version
            of that contract.
    """
    contract_type = contract_to_mock[contract_name]
    # In case of testnet/mainnet-fork, grab address from CONFIG
    if network.show_active() not in LOCAL_BLOCKCHAIN_DEVELOPMENT:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)
    # Working on local development, need to deploy mocks if not exist or grab latest deployed
    else:
        # No previous mock deployed, deploy one
        if len(contract_type) < 1:
            deploy_mocks()
        # Grab latest deployed mock
        contract = contract_type[-1]
    return contract


DECIMALS = 18
ETH_INITIAL_VALUE = 2000
DAI_INITIAL_VALUE = 1

contract_pricefeed_values_dic = {
    "eth_usd_price_feed": {"DECIMALS": DECIMALS, "INITIAL_VALUE": Web3.toWei(ETH_INITIAL_VALUE, "ether")},
    "dai_usd_price_feed": {"DECIMALS": DECIMALS, "INITIAL_VALUE": Web3.toWei(DAI_INITIAL_VALUE, "ether")},
}


def deploy_mocks():
    """
    We will deploy all relevant contracts mocks that we need in order to
    to run our contract in a forked envoirment
    """
    account = get_account()
    print("Deploying mocks...!")
    print("Deploying Mock V3 Aggregator...")
    for contract_name in contract_pricefeed_values_dic.values():
        eth_usd_aggregator = MockV3Aggregator.deploy(
            contract_name["DECIMALS"], contract_name["INITIAL_VALUE"], {"from": account}
        )
        print(f"ETH/USD Mock V3 Aggregator deployed at {eth_usd_aggregator.address}")
        dai_usd_aggregator = MockV3Aggregator.deploy(
            contract_name["DECIMALS"], contract_name["INITIAL_VALUE"], {"from": account}
        )
        print(f"DAI/USD Mock V3 Aggregator deployed at {dai_usd_aggregator.address}")
    print("Deploying Link Token Mock...")
    link = LinkToken.deploy({"from": account})
    print("Link Token Mock deployed at {}".format(link.address))
    print("Deploying FAU/MockDAI Mock...")
    fau = MockDAI.deploy({"from": account})
    print("FAU/MockDAI has beeb deployed at {}".format(fau.address))
    print("Deploying MockWETH Mock...")
    weth = MockWETH.deploy({"from": account})
    print("MockWETH has been deployed at {}".format(weth.address))
    print("*** All relevenat mocks has been deployed!!! ***")


LINK_VALUE = Web3.toWei(0.1, "ether")


def fund_with_link(contract_address, account=None, link_token=None, value=LINK_VALUE):
    """
    dev fund a contract with link token
    @para contract_address = contract address to fund (required)
    @para account = in case a specific account to send from otherwise using default
    @para link_token = in case of a specific link token address to use, otherwise default
    @para value = default 0.1 LINK
    """
    account = get_account()
    print("Funding contract with link...")
    link = link if link_token else get_contract(link_token)
    # Approving link spending token (...* 1.05 as a assurence consideration)
    if Web3.fromWei(link.balanceOf(contract_address), "ether") > Web3.fromWei(
        config["networks"][network.show_active()]["link_fee"], "ether"
    ):
        print(
            "Contract has enough Link tokens to cover fees, contract has: {} and fees are: {} !".format(
                Web3.fromWei(link.balanceOf(contract_address), config["networks"][network.show_active()]["link_fee"])
            )
        )
    else:
        tx = link.approve(account.address, value, {"from": account})
        tx.wait(1)
        tx = link.transfer(contract_address, value, {"from": account})
        tx.wait(1)
        print(
            "Contract address {} funded with link in an amount of {}!!".format(
                contract_address, Web3.fromWei(LINK_VALUE, "ether")
            )
        )
