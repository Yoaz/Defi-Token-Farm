from brownie import network, LinkToken, exceptions
from scripts.helpful_scripts import get_account, get_contract, LOCAL_BLOCKCHAIN_DEVELOPMENT
from scripts.deploy import deploy_token_farm_and_dapp
import pytest
from web3 import Web3

AMOUNT_TO_STAKE = 2


def test_set_price_feed():
    # Arrange
    account = get_account()
    non_owner = get_account(index=1)
    if network.show_active() not in LOCAL_BLOCKCHAIN_DEVELOPMENT:
        pytest.skip("Only for local testing!")
    # Act
    token_farm, dapp_token, dict_of_allowed_tokens = deploy_token_farm_and_dapp()
    tx = token_farm.setTokenPriceFeed(dapp_token.address, dict_of_allowed_tokens[dapp_token].address, {"from": account})
    tx.wait(1)
    # Assert
    assert token_farm.tokenPriceFeedMapping(dapp_token.address) == dict_of_allowed_tokens[dapp_token].address
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.setTokenPriceFeed(
            dapp_token.address, dict_of_allowed_tokens[dapp_token].address, {"from": non_owner}
        )


def test_can_stake_tokens():
    # Arrange
    account = get_account()
    non_owner = get_account(index=1)
    if network.show_active() not in LOCAL_BLOCKCHAIN_DEVELOPMENT:
        pytest.skip("Only for local testing!")  # unit test will be applied to development networks only
    token_farm = deploy_token_farm_and_dapp()
    # Act
    # Link token will be used to stake and test porpoises
    link_token = get_contract("link_token")
    token_farm.addAllowedTokens(link_token.address, {"from": account})
    approve_tx = link_token.approve(token_farm.address, Web3.toWei(AMOUNT_TO_STAKE, "ether"), {"from": account})
    approve_tx.wait(1)
    tx = token_farm.stakeTokens(Web3.toWei(AMOUNT_TO_STAKE, "ether"), link_token.address, {"from": account})
    tx.wait(1)
    print("Staked {} amount of tokens".format(AMOUNT_TO_STAKE))
    amount_staked = token_farm.stakingBalance(link_token.address, account.address)
    print(
        "User address {} has a total of {} staked".format(
            account.address, token_farm.getUserTotalValue(account.address)
        )
    )
    # Assert
    # Expected amount_staked == AMOUNT_TO_STAKE
    assert amount_staked == AMOUNT_TO_STAKE
