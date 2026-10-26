// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ModelProvenance
 * @notice On-chain registry of AI model fingerprints and version lineage.
 * @dev Authorization rule (MVP): the original creator of a model lineage may
 *      register subsequent versions. The contract owner may pause further
 *      registrations in an emergency but cannot rewrite existing records.
 */
contract ModelProvenance is Ownable {
    struct ModelRecord {
        bytes32 modelId;
        bytes32 modelHash;
        bytes32 metadataHash;
        address creator;
        uint256 version;
        bytes32 parentModelId;
        uint256 timestamp;
        bool exists;
    }

    mapping(bytes32 => ModelRecord) private _models;

    bool public registrationsPaused;

    event ModelRegistered(
        bytes32 indexed modelId,
        bytes32 modelHash,
        address indexed creator,
        uint256 version,
        bytes32 indexed parentModelId
    );

    event RegistrationsPaused(bool paused);

    error ModelAlreadyExists(bytes32 modelId);
    error ModelNotFound(bytes32 modelId);
    error InvalidModelId();
    error InvalidModelHash();
    error InvalidMetadataHash();
    error InvalidParentModelId();
    error ParentModelNotFound(bytes32 parentModelId);
    error UnauthorizedVersionCreator(address caller, address creator);
    error InvalidVersionNumber(uint256 provided, uint256 expected);
    error RegistrationsArePaused();
    error ZeroAddressCreator();

    modifier whenRegistrationsActive() {
        if (registrationsPaused) {
            revert RegistrationsArePaused();
        }
        _;
    }

    constructor(address initialOwner) Ownable(initialOwner) {}

    /**
     * @notice Register a new root model (version 1, no parent).
     */
    function registerModel(
        bytes32 modelId,
        bytes32 modelHash,
        bytes32 metadataHash
    ) external whenRegistrationsActive returns (bool) {
        _validateNewIdentity(modelId, modelHash, metadataHash);
        if (_models[modelId].exists) {
            revert ModelAlreadyExists(modelId);
        }

        address creator = msg.sender;
        if (creator == address(0)) {
            revert ZeroAddressCreator();
        }

        _models[modelId] = ModelRecord({
            modelId: modelId,
            modelHash: modelHash,
            metadataHash: metadataHash,
            creator: creator,
            version: 1,
            parentModelId: bytes32(0),
            timestamp: block.timestamp,
            exists: true
        });

        emit ModelRegistered(modelId, modelHash, creator, 1, bytes32(0));
        return true;
    }

    /**
     * @notice Register a new version linked to an existing parent model.
     * @dev Only the parent lineage creator may register versions. Prior records
     *      are never overwritten.
     */
    function registerVersion(
        bytes32 modelId,
        bytes32 modelHash,
        bytes32 metadataHash,
        bytes32 parentModelId,
        uint256 version
    ) external whenRegistrationsActive returns (bool) {
        _validateNewIdentity(modelId, modelHash, metadataHash);

        if (parentModelId == bytes32(0)) {
            revert InvalidParentModelId();
        }
        if (!_models[parentModelId].exists) {
            revert ParentModelNotFound(parentModelId);
        }
        if (_models[modelId].exists) {
            revert ModelAlreadyExists(modelId);
        }

        ModelRecord storage parent = _models[parentModelId];
        if (msg.sender != parent.creator) {
            revert UnauthorizedVersionCreator(msg.sender, parent.creator);
        }

        uint256 expectedVersion = parent.version + 1;
        if (version != expectedVersion) {
            revert InvalidVersionNumber(version, expectedVersion);
        }

        _models[modelId] = ModelRecord({
            modelId: modelId,
            modelHash: modelHash,
            metadataHash: metadataHash,
            creator: parent.creator,
            version: version,
            parentModelId: parentModelId,
            timestamp: block.timestamp,
            exists: true
        });

        emit ModelRegistered(modelId, modelHash, parent.creator, version, parentModelId);
        return true;
    }

    /**
     * @notice Return a registered model record.
     */
    function getModel(
        bytes32 modelId
    )
        external
        view
        returns (
            bytes32 outModelId,
            bytes32 modelHash,
            bytes32 metadataHash,
            address creator,
            uint256 version,
            bytes32 parentModelId,
            uint256 timestamp,
            bool exists
        )
    {
        ModelRecord storage record = _models[modelId];
        if (!record.exists) {
            revert ModelNotFound(modelId);
        }

        return (
            record.modelId,
            record.modelHash,
            record.metadataHash,
            record.creator,
            record.version,
            record.parentModelId,
            record.timestamp,
            record.exists
        );
    }

    /**
     * @notice Compare a supplied fingerprint against the registered model hash.
     * @return matched True when the supplied hash equals the on-chain fingerprint.
     */
    function verifyModel(
        bytes32 modelId,
        bytes32 modelHash
    ) external view returns (bool matched) {
        ModelRecord storage record = _models[modelId];
        if (!record.exists) {
            revert ModelNotFound(modelId);
        }
        if (modelHash == bytes32(0)) {
            revert InvalidModelHash();
        }
        return record.modelHash == modelHash;
    }

    /**
     * @notice Owner may pause or resume new registrations (existing records stay intact).
     */
    function setRegistrationsPaused(bool paused) external onlyOwner {
        registrationsPaused = paused;
        emit RegistrationsPaused(paused);
    }

    function _validateNewIdentity(
        bytes32 modelId,
        bytes32 modelHash,
        bytes32 metadataHash
    ) private pure {
        if (modelId == bytes32(0)) {
            revert InvalidModelId();
        }
        if (modelHash == bytes32(0)) {
            revert InvalidModelHash();
        }
        if (metadataHash == bytes32(0)) {
            revert InvalidMetadataHash();
        }
    }
}
