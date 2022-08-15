// SPDX-License-Identifier: MIT

pragma solidity ^0.8.7;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract TokenFarm is Ownable {
    IERC20 public dappToken;
    uint256 stakersMappingIndex;
    address[] public stakers;
    mapping(address => uint256) public indexOfStaker;
    address[] public allowedTokens;
    mapping(address => mapping(address => uint256)) public stakingBalance;
    mapping(address => uint256) public uniqueTokenStaked;
    mapping(address => address) public tokenPriceFeedMapping;

    constructor(address _dappTokenAddress) {
        dappToken = IERC20(_dappTokenAddress);
        stakersMappingIndex = 0;
    }

    function setTokenPriceFeed(address _token, address _priceFeed)
        public
        onlyOwner
    {
        tokenPriceFeedMapping[_token] = _priceFeed;
    }

    function addAllowedTokens(address _token) public onlyOwner {
        allowedTokens.push(_token);
    }

    function stakeTokens(uint256 _amount, address _token) public {
        require(_amount > 0, "Amount needs to be greater than 0");
        require(tokenIsAllowed(_token), "Token currently isn't allowed");
        updateUniqueTokensStaked(msg.sender, _token);
        stakingBalance[_token][msg.sender] += _amount;
        if (uniqueTokenStaked[msg.sender] == 1) {
            stakers.push(msg.sender);
            // Increase stakers mapping index and save in index of stakers mapping based on user's address
            stakersMappingIndex += 1;
            indexOfStaker[msg.sender] = stakersMappingIndex;
        }
    }

    function updateUniqueTokensStaked(address _user, address _token)
        internal
        onlyOwner
    {
        // pre-check if already staking the current token
        if (stakingBalance[_token][_user] <= 0) {
            uniqueTokenStaked[_user] += 1;
        }
    }

    function tokenIsAllowed(address _token) internal view returns (bool) {
        for (
            uint256 allowedTokensIndex = 0;
            allowedTokensIndex < allowedTokens.length;
            allowedTokensIndex++
        ) {
            if (allowedTokens[allowedTokensIndex] == _token) {
                return true;
            }
        }
        return false;
    }

    function issueTokens() public onlyOwner {
        for (
            uint256 stakersIndex = 0;
            stakersIndex < stakers.length;
            stakersIndex++
        ) {
            address recipient = stakers[stakersIndex];
            dappToken.transfer(recipient, getUserTotalValue(recipient));
        }
    }

    function getUserTotalValue(address _user) public view returns (uint256) {
        require(uniqueTokenStaked[_user] > 0, "No staked tokens!");
        uint256 totalValue = 0;
        for (
            uint256 tokensIndex = 0;
            tokensIndex < allowedTokens.length;
            tokensIndex++
        ) {
            address tokenAddress = allowedTokens[tokensIndex];
            totalValue += getUserSingleTokenValue(_user, tokenAddress);
        }
        return totalValue;
    }

    function getUserSingleTokenValue(address _user, address _token)
        public
        view
        returns (uint256)
    {
        if (stakingBalance[_token][_user] <= 0) {
            return 0;
        }
        (uint256 tokenUsdValue, uint256 tokenDecimals) = getTokenValue(_token);
        // ex. 1ETH staked => (1 * eth_usd_value) / 1000000000000000000
        return
            (stakingBalance[_token][_user] * tokenUsdValue) /
            (10**tokenDecimals);
    }

    function getTokenValue(address _token)
        public
        view
        returns (uint256, uint256)
    {
        address priceFeedAdress = tokenPriceFeedMapping[_token];
        AggregatorV3Interface priceFeed = AggregatorV3Interface(
            priceFeedAdress
        );
        (, int256 price, , , ) = priceFeed.latestRoundData();
        uint256 decimals = priceFeed.decimals();
        return (uint256(price), decimals);
    }

    function unstakeTokens(address _token) public {
        // Require some tokens been staked
        require(
            uniqueTokenStaked[msg.sender] > 0,
            "No staked tokens for this account!"
        );
        // Require balance of _token greater than 0
        require(
            stakingBalance[_token][msg.sender] > 0,
            "Staking balance cannot be 0!"
        );
        // Transfer token balance back to user
        IERC20(_token).transfer(msg.sender, stakingBalance[_token][msg.sender]);
        // Update staking balance
        stakingBalance[_token][msg.sender] = 0;
        uniqueTokenStaked[msg.sender] -= 1;
        // if no tokens staked after unstaking
        if (uniqueTokenStaked[msg.sender] < 1) {
            removeStaker(msg.sender);
        }
    }

    function removeStaker(address _user) internal onlyOwner {
        // stakers[][*][][][] = stakers[][][][][*]
        stakers[indexOfStaker[_user]] = stakers[stakers.length - 1];
        stakers.pop();
        // remove user from index of staker mapping
        delete indexOfStaker[_user];
    }
}
