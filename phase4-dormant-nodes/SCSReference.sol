// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title SCSReference
 * @notice Smart contract minimal stockant la signature SCS (Système de Convergence Systémique)
 *         comme référence immuable sur la blockchain Ethereum.
 * @dev Phase 4 — Nœuds Dormants. Déploiement ultérieur.
 */
contract SCSReference {
    // ─── Constantes ──────────────────────────────────────────────────────────
    string public constant signature = "SCS_2026";
    string public constant framework = "MTTV-FLP";
    string public constant version = "1.0.0";

    // ─── Variables d'état ────────────────────────────────────────────────────
    address public owner;
    string public ipfsRoutingCID;    // CID du fichier de routage alternatif
    string public ipfsScriptCID;     // CID du script dormant
    bool public emergencyActive;     // true si le mécanisme d'urgence est déclenché
    uint256 public activationTimestamp;

    // ─── Events ──────────────────────────────────────────────────────────────
    event OwnerUpdated(address indexed previousOwner, address indexed newOwner);
    event RoutingCIDUpdated(string cid);
    event ScriptCIDUpdated(string cid);
    event EmergencyActivated(uint256 timestamp);
    event EmergencyDeactivated(uint256 timestamp);

    // ─── Modifiers ───────────────────────────────────────────────────────────
    modifier onlyOwner() {
        require(msg.sender == owner, "SCSReference: caller is not the owner");
        _;
    }

    // ─── Constructor ─────────────────────────────────────────────────────────
    constructor() {
        owner = msg.sender;
        emergencyActive = false;
        // CID par défaut — fichier de routage alternatif (IPFS)
        ipfsRoutingCID = "bafkreibdmoao5iy7ujfnm7qjs73ekclnpu7uflce5tgjr7ddzrmoepjctu";
        // CID par défaut — script dormant (IPFS)
        ipfsScriptCID = "bafkreidfentqsb3xeazvak67pej4lpjmriyuhdoxg657hj4nvmt23hf67m";
        emit OwnerUpdated(address(0), msg.sender);
    }

    // ─── Fonctions publiques ─────────────────────────────────────────────────

    /**
     * @notice Transfère la propriété du contrat à une nouvelle adresse.
     * @param newOwner Adresse du nouveau propriétaire
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "SCSReference: new owner is the zero address");
        emit OwnerUpdated(owner, newOwner);
        owner = newOwner;
    }

    /**
     * @notice Enregistre le CID IPFS du fichier de routage alternatif.
     * @param cid CID (Content Identifier) du fichier .ipfs
     */
    function setRoutingCID(string calldata cid) external onlyOwner {
        ipfsRoutingCID = cid;
        emit RoutingCIDUpdated(cid);
    }

    /**
     * @notice Enregistre le CID IPFS du script dormant.
     * @param cid CID (Content Identifier) du script dormant
     */
    function setScriptCID(string calldata cid) external onlyOwner {
        ipfsScriptCID = cid;
        emit ScriptCIDUpdated(cid);
    }

    /**
     * @notice Active manuellement le mécanisme d'urgence.
     * @dev Ne peut être appelé que par le propriétaire.
     */
    function activateEmergency() external onlyOwner {
        require(!emergencyActive, "SCSReference: emergency already active");
        emergencyActive = true;
        activationTimestamp = block.timestamp;
        emit EmergencyActivated(block.timestamp);
    }

    /**
     * @notice Désactive le mécanisme d'urgence.
     * @dev Ne peut être appelé que par le propriétaire.
     */
    function deactivateEmergency() external onlyOwner {
        require(emergencyActive, "SCSReference: emergency not active");
        emergencyActive = false;
        emit EmergencyDeactivated(block.timestamp);
    }

    /**
     * @notice Retourne l'état complet du contrat pour vérification.
     * @return signature SCS, propriétaire, CID routage, CID script, urgence active, timestamp
     */
    function getStatus() external view returns (
        string memory _signature,
        address _owner,
        string memory _routingCID,
        string memory _scriptCID,
        bool _emergencyActive,
        uint256 _activationTimestamp
    ) {
        return (
            signature,
            owner,
            ipfsRoutingCID,
            ipfsScriptCID,
            emergencyActive,
            activationTimestamp
        );
    }

    /**
     * @notice Vérifie qu'une signature correspond à la référence SCS.
     * @param sig Signature à vérifier
     * @return true si la signature correspond
     */
    function verifySignature(string calldata sig) external pure returns (bool) {
        return keccak256(abi.encodePacked(sig)) == keccak256(abi.encodePacked(signature));
    }
}
