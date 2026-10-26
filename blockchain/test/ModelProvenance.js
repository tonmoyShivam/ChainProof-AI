const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");

const ZERO = ethers.ZeroHash;

function id(label) {
  return ethers.id(label);
}

function hash(label) {
  return ethers.id(`hash:${label}`);
}

function meta(label) {
  return ethers.id(`meta:${label}`);
}

async function deployFixture() {
  const [owner, creator, stranger] = await ethers.getSigners();
  const Factory = await ethers.getContractFactory("ModelProvenance");
  const registry = await Factory.deploy(owner.address);
  await registry.waitForDeployment();
  return { registry, owner, creator, stranger };
}

describe("ModelProvenance", function () {
  describe("registerModel", function () {
    it("registers a root model successfully", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      const modelId = id("model-v1");
      const modelHash = hash("weights-v1");
      const metadataHash = meta("meta-v1");

      await expect(registry.connect(creator).registerModel(modelId, modelHash, metadataHash))
        .to.emit(registry, "ModelRegistered")
        .withArgs(modelId, modelHash, creator.address, 1n, ZERO);

      const record = await registry.getModel(modelId);
      expect(record.outModelId).to.equal(modelId);
      expect(record.modelHash).to.equal(modelHash);
      expect(record.metadataHash).to.equal(metadataHash);
      expect(record.creator).to.equal(creator.address);
      expect(record.version).to.equal(1n);
      expect(record.parentModelId).to.equal(ZERO);
      expect(record.exists).to.equal(true);
    });

    it("rejects duplicate model IDs", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      const modelId = id("dup");
      await registry.connect(creator).registerModel(modelId, hash("a"), meta("a"));
      await expect(
        registry.connect(creator).registerModel(modelId, hash("b"), meta("b"))
      ).to.be.revertedWithCustomError(registry, "ModelAlreadyExists");
    });

    it("rejects empty / zero model hashes", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      await expect(
        registry.connect(creator).registerModel(id("m"), ZERO, meta("m"))
      ).to.be.revertedWithCustomError(registry, "InvalidModelHash");
    });

    it("rejects zero model IDs and zero metadata digests", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      await expect(
        registry.connect(creator).registerModel(ZERO, hash("m"), meta("m"))
      ).to.be.revertedWithCustomError(registry, "InvalidModelId");
      await expect(
        registry.connect(creator).registerModel(id("m"), hash("m"), ZERO)
      ).to.be.revertedWithCustomError(registry, "InvalidMetadataHash");
    });
  });

  describe("verifyModel", function () {
    it("returns true for a matching hash", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      const modelId = id("verify-ok");
      const modelHash = hash("ok");
      await registry.connect(creator).registerModel(modelId, modelHash, meta("ok"));
      expect(await registry.verifyModel(modelId, modelHash)).to.equal(true);
    });

    it("returns false for a mismatched hash", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      const modelId = id("verify-bad");
      await registry.connect(creator).registerModel(modelId, hash("original"), meta("x"));
      expect(await registry.verifyModel(modelId, hash("tampered"))).to.equal(false);
    });

    it("rejects verification of an unknown model", async function () {
      const { registry } = await loadFixture(deployFixture);
      await expect(
        registry.verifyModel(id("missing"), hash("anything"))
      ).to.be.revertedWithCustomError(registry, "ModelNotFound");
    });
  });

  describe("registerVersion", function () {
    it("allows the authorized creator to register a linked version", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      const parentId = id("root");
      const childId = id("child");
      const parentHash = hash("root");
      const childHash = hash("child");

      await registry.connect(creator).registerModel(parentId, parentHash, meta("root"));
      await expect(
        registry
          .connect(creator)
          .registerVersion(childId, childHash, meta("child"), parentId, 2)
      )
        .to.emit(registry, "ModelRegistered")
        .withArgs(childId, childHash, creator.address, 2n, parentId);

      const child = await registry.getModel(childId);
      expect(child.version).to.equal(2n);
      expect(child.parentModelId).to.equal(parentId);
      expect(child.creator).to.equal(creator.address);
    });

    it("rejects unauthorized version registration", async function () {
      const { registry, creator, stranger } = await loadFixture(deployFixture);
      const parentId = id("owned");
      await registry.connect(creator).registerModel(parentId, hash("p"), meta("p"));
      await expect(
        registry
          .connect(stranger)
          .registerVersion(id("v2"), hash("v2"), meta("v2"), parentId, 2)
      ).to.be.revertedWithCustomError(registry, "UnauthorizedVersionCreator");
    });

    it("rejects missing parent records", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      await expect(
        registry
          .connect(creator)
          .registerVersion(id("orphan"), hash("o"), meta("o"), id("no-parent"), 2)
      ).to.be.revertedWithCustomError(registry, "ParentModelNotFound");
    });

    it("preserves previous records after a new version is registered", async function () {
      const { registry, creator } = await loadFixture(deployFixture);
      const parentId = id("preserve-root");
      const childId = id("preserve-child");
      const parentHash = hash("preserve-root");
      const parentMeta = meta("preserve-root");

      await registry.connect(creator).registerModel(parentId, parentHash, parentMeta);
      const before = await registry.getModel(parentId);

      await registry
        .connect(creator)
        .registerVersion(childId, hash("preserve-child"), meta("preserve-child"), parentId, 2);

      const after = await registry.getModel(parentId);
      expect(after.modelHash).to.equal(before.modelHash);
      expect(after.metadataHash).to.equal(before.metadataHash);
      expect(after.version).to.equal(before.version);
      expect(after.creator).to.equal(before.creator);
      expect(after.parentModelId).to.equal(ZERO);
      expect(after.exists).to.equal(true);

      // Parent fingerprint still verifies independently of the child.
      expect(await registry.verifyModel(parentId, parentHash)).to.equal(true);
      expect(await registry.verifyModel(childId, hash("preserve-child"))).to.equal(true);
    });
  });

  describe("getModel", function () {
    it("reverts for unknown models", async function () {
      const { registry } = await loadFixture(deployFixture);
      await expect(registry.getModel(id("unknown"))).to.be.revertedWithCustomError(
        registry,
        "ModelNotFound"
      );
    });
  });

  describe("owner pause", function () {
    it("lets the owner pause registrations without altering records", async function () {
      const { registry, owner, creator } = await loadFixture(deployFixture);
      const modelId = id("pause-me");
      await registry.connect(creator).registerModel(modelId, hash("p"), meta("p"));

      await registry.connect(owner).setRegistrationsPaused(true);
      await expect(
        registry.connect(creator).registerModel(id("after-pause"), hash("x"), meta("x"))
      ).to.be.revertedWithCustomError(registry, "RegistrationsArePaused");

      const record = await registry.getModel(modelId);
      expect(record.exists).to.equal(true);
      expect(await registry.verifyModel(modelId, hash("p"))).to.equal(true);
    });
  });
});
