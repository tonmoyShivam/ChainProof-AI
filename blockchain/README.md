# VerityAI Blockchain Package

Hardhat workspace for the VerityAI provenance registry (local EVM).

## Milestone 3 status

- `contracts/ModelProvenance.sol` — on-chain fingerprint + version lineage registry
- OpenZeppelin `Ownable` for emergency pause of new registrations
- Hardhat tests covering success, duplicates, empty hashes, verify match/mismatch, unknown models, authorized/unauthorized versions, parent linkage, and record preservation
- Deploy script for the local Hardhat network (`chainId` 31337)

### Authorization rules (MVP)

- Anyone may register a **root** model (`registerModel`); `msg.sender` becomes that lineage’s creator.
- Only the **parent lineage creator** may call `registerVersion`.
- The contract **owner** may pause/unpause new registrations; existing records are never rewritten.

## Commands

```bash
# Install dependencies (see .npmrc for peer-dep resolution)
npm install

# Compile
npx hardhat compile

# Unit tests
npx hardhat test

# Start a local Hardhat node (RPC http://127.0.0.1:8545)
npx hardhat node

# Deploy to that node (separate terminal)
npx hardhat run scripts/deploy.js --network localhost
```

After deploy, copy the printed address into the root `.env` as `BLOCKCHAIN_CONTRACT_ADDRESS` (used in Milestone 4+). Deployment JSON is written under `blockchain/deployments/` (gitignored).

### npm scripts

```bash
npm run compile
npm test
npm run node
npm run deploy:localhost
```
