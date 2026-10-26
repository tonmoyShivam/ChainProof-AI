/**
 * Deploy ModelProvenance to the configured Hardhat network.
 *
 * Local node:
 *   Terminal A: npx hardhat node
 *   Terminal B: npx hardhat run scripts/deploy.js --network localhost
 *
 * In-process Hardhat network (ephemeral):
 *   npx hardhat run scripts/deploy.js
 */
const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const network = await hre.ethers.provider.getNetwork();

  console.log(`Deploying ModelProvenance with account: ${deployer.address}`);
  console.log(`Network chainId: ${network.chainId}`);

  const Factory = await hre.ethers.getContractFactory("ModelProvenance");
  const registry = await Factory.deploy(deployer.address);
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log(`ModelProvenance deployed to: ${address}`);

  const deploymentsDir = path.join(__dirname, "..", "deployments");
  fs.mkdirSync(deploymentsDir, { recursive: true });
  const outPath = path.join(deploymentsDir, `ModelProvenance-${network.chainId}.json`);
  const payload = {
    contract: "ModelProvenance",
    address,
    chainId: Number(network.chainId),
    deployer: deployer.address,
    deployedAt: new Date().toISOString(),
  };
  fs.writeFileSync(outPath, `${JSON.stringify(payload, null, 2)}\n`);
  console.log(`Wrote deployment record: ${outPath}`);
  console.log(
    "Set BLOCKCHAIN_CONTRACT_ADDRESS in your root .env to the address above for later milestones."
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
