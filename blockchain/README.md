# VerityAI Blockchain Package

Hardhat workspace for the VerityAI provenance registry (local EVM).

## Milestone 1 status

- Hardhat 2.22.x initialized with Solidity 0.8.24
- Local network config (`chainId` 31337)
- Smart contracts (`ModelProvenance.sol`) arrive in **Milestone 3**

## Commands

```bash
# Install dependencies
npm install

# Start a local Hardhat node (RPC on http://127.0.0.1:8545)
npx hardhat node

# Compile contracts (once contracts exist)
npx hardhat compile

# Run contract tests
npx hardhat test
```
