from brownie import network, TokenFarm, DappToken, config
from scripts.helpful_scripts import get_account, get_contract
from web3 import Web3

KEPT_BALANCE = Web3.toWei(100, "ether")


def deploy_token_farm_and_dapp():
    account = get_account()
    print("Deploying contract...")
    dapp_token = DappToken.deploy(
        {"from": account}, publish_source=config["networks"][network.show_active()].get("verify", False)
    )
    token_farm = TokenFarm.deploy(
        dapp_token.address,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verfy", False),
    )
    print(f"Contract deployed at address: {token_farm.address}!")
    # Transfer most of the DAPP Token to our TokenFarm contract so it could be rewarded based on user's staking
    transfer_tx = dapp_token.transfer(token_farm.address, dapp_token.totalSupply() - KEPT_BALANCE, {"from": account})
    transfer_tx.wait(1)
    fau_token = get_contract("fau_token")
    weth_token = get_contract("weth_token")
    dict_of_allowed_tokens = {
        dapp_token: get_contract("dai_usd_price_feed"),
        fau_token: get_contract("dai_usd_price_feed"),
        weth_token: get_contract("eth_usd_price_feed"),
    }
    add_allowed_tokens(token_farm, dict_of_allowed_tokens, account)
    return token_farm, dapp_token, dict_of_allowed_tokens


def add_allowed_tokens(token_farm, dic_allowed_tokens, account):
    for token in dic_allowed_tokens:
        add_tx = token_farm.addAllowedTokens(token.address, {"from": account})
        add_tx.wait(1)
        set_tx = token_farm.setTokenPriceFeed(token.address, dic_allowed_tokens[token].address, {"from": account})
        set_tx.wait(1)
    return token_farm


def main():
    deploy_token_farm_and_dapp()
