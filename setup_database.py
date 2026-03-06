"""
Database initialization module.
Handles schema definition and population of initial records
for the space station logistics system.
"""

import sqlite3
import datetime
import random

DATABASE_FILE = 'space_station_supply.db'


def _build_table_definitions():
    """
    Constructs and returns a list of CREATE TABLE statements
    that define the entire relational schema for the supply system.
    """
    captains_ddl = """CREATE TABLE IF NOT EXISTS Captains (
        CaptainId INTEGER PRIMARY KEY AUTOINCREMENT,
        CaptainCode TEXT UNIQUE NOT NULL,
        CaptainName TEXT NOT NULL,
        CommsChannel TEXT,
        ShipRegistry TEXT,
        HomePlanet TEXT,
        AllianceAffiliation TEXT,
        Rank TEXT,
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        IsActive INTEGER NOT NULL DEFAULT 1
    );"""

    merchants_ddl = """CREATE TABLE IF NOT EXISTS Merchants (
        MerchantId INTEGER PRIMARY KEY AUTOINCREMENT,
        MerchantCode TEXT UNIQUE NOT NULL,
        MerchantName TEXT NOT NULL,
        CommsChannel TEXT,
        GuildName TEXT,
        PrimaryHub TEXT,
        Sector TEXT,
        System TEXT,
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        IsActive INTEGER NOT NULL DEFAULT 1
    );"""

    stations_ddl = """CREATE TABLE IF NOT EXISTS Stations (
        StationId INTEGER PRIMARY KEY AUTOINCREMENT,
        StationCode TEXT UNIQUE NOT NULL,
        StationName TEXT NOT NULL,
        OrbitingBody TEXT,
        System TEXT,
        Galaxy TEXT,
        LocalTimeCycle TEXT,
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        IsActive INTEGER NOT NULL DEFAULT 1
    );"""

    sectors_ddl = """CREATE TABLE IF NOT EXISTS Sectors (
        SectorId INTEGER PRIMARY KEY AUTOINCREMENT,
        StationId INTEGER NOT NULL,
        SectorCode TEXT NOT NULL,
        SectorName TEXT NOT NULL,
        ParentSectorId INTEGER,
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        IsActive INTEGER NOT NULL DEFAULT 1,
        UNIQUE (StationId, SectorCode),
        FOREIGN KEY (StationId) REFERENCES Stations(StationId),
        FOREIGN KEY (ParentSectorId) REFERENCES Sectors(SectorId)
    );"""

    cargo_ddl = """CREATE TABLE IF NOT EXISTS CargoTypes (
        CargoId INTEGER PRIMARY KEY AUTOINCREMENT,
        CargoCode TEXT UNIQUE NOT NULL,
        CargoName TEXT NOT NULL,
        MatterState TEXT,
        StorageUnit TEXT,
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        IsActive INTEGER NOT NULL DEFAULT 1
    );"""

    equipment_ddl = """CREATE TABLE IF NOT EXISTS Equipment (
        EquipId INTEGER PRIMARY KEY AUTOINCREMENT,
        EquipTag TEXT UNIQUE NOT NULL,
        EquipName TEXT NOT NULL,
        StationId INTEGER NOT NULL,
        SectorId INTEGER,
        SerialDesignation TEXT,
        Category TEXT,
        OperationalStatus TEXT NOT NULL DEFAULT 'Online',
        CreditValue DECIMAL(18,2),
        CommissionDate DATE,
        MerchantId INTEGER,
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        FOREIGN KEY (StationId) REFERENCES Stations(StationId),
        FOREIGN KEY (SectorId) REFERENCES Sectors(SectorId),
        FOREIGN KEY (MerchantId) REFERENCES Merchants(MerchantId)
    );"""

    invoices_ddl = """CREATE TABLE IF NOT EXISTS Invoices (
        InvoiceId INTEGER PRIMARY KEY AUTOINCREMENT,
        MerchantId INTEGER NOT NULL,
        InvoiceNumber TEXT NOT NULL,
        InvoiceCycle DATE NOT NULL,
        CycleEnd DATE,
        TotalCredits DECIMAL(18,2) NOT NULL,
        Currency TEXT NOT NULL DEFAULT 'GalacticCredits',
        Status TEXT NOT NULL DEFAULT 'Pending',
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        UNIQUE (MerchantId, InvoiceNumber),
        FOREIGN KEY (MerchantId) REFERENCES Merchants(MerchantId)
    );"""

    supply_contracts_ddl = """CREATE TABLE IF NOT EXISTS SupplyContracts (
        ContractId INTEGER PRIMARY KEY AUTOINCREMENT,
        ContractNumber TEXT NOT NULL UNIQUE,
        MerchantId INTEGER NOT NULL,
        RatificationDate DATE NOT NULL,
        Status TEXT NOT NULL DEFAULT 'Active',
        StationId INTEGER,
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        FOREIGN KEY (MerchantId) REFERENCES Merchants(MerchantId),
        FOREIGN KEY (StationId) REFERENCES Stations(StationId)
    );"""

    contract_lines_ddl = """CREATE TABLE IF NOT EXISTS SupplyContractLines (
        LineId INTEGER PRIMARY KEY AUTOINCREMENT,
        ContractId INTEGER NOT NULL,
        LineSequence INTEGER NOT NULL,
        CargoId INTEGER,
        CargoCode TEXT NOT NULL,
        ManifestDetails TEXT,
        MassVolume DECIMAL(18,4) NOT NULL,
        CreditPerUnit DECIMAL(18,4) NOT NULL,
        UNIQUE (ContractId, LineSequence),
        FOREIGN KEY (ContractId) REFERENCES SupplyContracts(ContractId),
        FOREIGN KEY (CargoId) REFERENCES CargoTypes(CargoId)
    );"""

    trade_agreements_ddl = """CREATE TABLE IF NOT EXISTS TradeAgreements (
        AgreementId INTEGER PRIMARY KEY AUTOINCREMENT,
        AgreementNumber TEXT NOT NULL UNIQUE,
        CaptainId INTEGER NOT NULL,
        AgreementDate DATE NOT NULL,
        Status TEXT NOT NULL DEFAULT 'Open',
        StationId INTEGER,
        CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME,
        FOREIGN KEY (CaptainId) REFERENCES Captains(CaptainId),
        FOREIGN KEY (StationId) REFERENCES Stations(StationId)
    );"""

    agreement_lines_ddl = """CREATE TABLE IF NOT EXISTS TradeAgreementLines (
        AgreementLineId INTEGER PRIMARY KEY AUTOINCREMENT,
        AgreementId INTEGER NOT NULL,
        LineSequence INTEGER NOT NULL,
        CargoId INTEGER,
        CargoCode TEXT NOT NULL,
        ManifestDetails TEXT,
        MassVolume DECIMAL(18,4) NOT NULL,
        CreditPerUnit DECIMAL(18,4) NOT NULL,
        UNIQUE (AgreementId, LineSequence),
        FOREIGN KEY (AgreementId) REFERENCES TradeAgreements(AgreementId),
        FOREIGN KEY (CargoId) REFERENCES CargoTypes(CargoId)
    );"""

    transfers_ddl = """CREATE TABLE IF NOT EXISTS EquipmentTransfers (
        TransferId INTEGER PRIMARY KEY AUTOINCREMENT,
        EquipId INTEGER NOT NULL,
        FromSectorId INTEGER,
        ToSectorId INTEGER,
        TransferType TEXT NOT NULL,
        UnitCount INTEGER NOT NULL DEFAULT 1,
        TransferCycle DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        LogEntry TEXT,
        FOREIGN KEY (EquipId) REFERENCES Equipment(EquipId),
        FOREIGN KEY (FromSectorId) REFERENCES Sectors(SectorId),
        FOREIGN KEY (ToSectorId) REFERENCES Sectors(SectorId)
    );"""

    return [
        captains_ddl, merchants_ddl, stations_ddl, sectors_ddl,
        cargo_ddl, equipment_ddl, invoices_ddl, supply_contracts_ddl,
        contract_lines_ddl, trade_agreements_ddl, agreement_lines_ddl,
        transfers_ddl
    ]


def initialize_tables(db_cursor):
    """Execute all DDL statements to set up the relational schema."""
    ddl_commands = _build_table_definitions()
    for ddl in ddl_commands:
        db_cursor.execute(ddl)


def _insert_if_absent(db_cursor, sql_statement):
    """Helper to run an INSERT OR IGNORE and swallow duplicates."""
    db_cursor.execute(sql_statement)


def populate_sample_records(db_cursor):
    """Fills every table with representative sample rows."""

    # ---- Stations ----
    station_rows = [
        "INSERT OR IGNORE INTO Stations (StationCode, StationName, OrbitingBody, System) "
        "VALUES ('STN-Alpha', 'Alpha Centauri Hub', 'Proxima Centauri b', 'Alpha Centauri')",
        "INSERT OR IGNORE INTO Stations (StationCode, StationName, OrbitingBody, System) "
        "VALUES ('STN-Omega', 'Omega Deep Space Post', 'Nebula X-9', 'Orion Cygnus')",
        "INSERT OR IGNORE INTO Stations (StationCode, StationName, OrbitingBody, System) "
        "VALUES ('STN-Epsilon', 'Epsilon Mining Outpost', 'Asteroid Belt 7', 'Sirius')",
        "INSERT OR IGNORE INTO Stations (StationCode, StationName, OrbitingBody, System) "
        "VALUES ('STN-Zeta', 'Zeta Core Reactor', 'Gas Giant Zeta', 'Vega')",
    ]
    for row in station_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Sectors ----
    sector_rows = [
        "INSERT OR IGNORE INTO Sectors (StationId, SectorCode, SectorName) VALUES (1, 'SEC-01', 'Docking Bay A')",
        "INSERT OR IGNORE INTO Sectors (StationId, SectorCode, SectorName) VALUES (2, 'SEC-02', 'Cryo Storage Block')",
        "INSERT OR IGNORE INTO Sectors (StationId, SectorCode, SectorName) VALUES (3, 'SEC-03', 'Refinery Deck')",
        "INSERT OR IGNORE INTO Sectors (StationId, SectorCode, SectorName) VALUES (4, 'SEC-04', 'Energy Core Alpha')",
        "INSERT OR IGNORE INTO Sectors (StationId, SectorCode, SectorName) VALUES (1, 'SEC-05', 'Command Center')",
    ]
    for row in sector_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Captains ----
    captain_rows = [
        "INSERT OR IGNORE INTO Captains (CaptainCode, CaptainName, CommsChannel) "
        "VALUES ('CPT-001', 'Captain James T.', 'Freq-492')",
        "INSERT OR IGNORE INTO Captains (CaptainCode, CaptainName, CommsChannel) "
        "VALUES ('CPT-002', 'Han S.', 'Freq-1138')",
        "INSERT OR IGNORE INTO Captains (CaptainCode, CaptainName, CommsChannel, ShipRegistry, HomePlanet) "
        "VALUES ('CPT-003', 'Mal Reynolds', 'Freq-500', 'Serenity', 'Shadow')",
        "INSERT OR IGNORE INTO Captains (CaptainCode, CaptainName, CommsChannel, ShipRegistry, HomePlanet) "
        "VALUES ('CPT-004', 'Ellen Ripley', 'Freq-426', 'Nostromo', 'Earth')",
        "INSERT OR IGNORE INTO Captains (CaptainCode, CaptainName, CommsChannel, ShipRegistry, HomePlanet) "
        "VALUES ('CPT-005', 'Arthur Dent', 'Freq-42', 'Heart of Gold', 'Earth')",
    ]
    for row in captain_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Merchants ----
    merchant_rows = [
        "INSERT OR IGNORE INTO Merchants (MerchantCode, MerchantName, CommsChannel) "
        "VALUES ('MER-001', 'Galactic Supplies Co.', 'Freq-999')",
        "INSERT OR IGNORE INTO Merchants (MerchantCode, MerchantName, CommsChannel) "
        "VALUES ('MER-002', 'Outer Rim Trade Federation', 'Freq-777')",
        "INSERT OR IGNORE INTO Merchants (MerchantCode, MerchantName, GuildName, Sector) "
        "VALUES ('MER-003', 'Sirius Cybernetics Corp', 'Tech Guild', 'Core Worlds')",
        "INSERT OR IGNORE INTO Merchants (MerchantCode, MerchantName, GuildName, Sector) "
        "VALUES ('MER-004', 'Weyland-Yutani', 'Corporate', 'Deep Space')",
    ]
    for row in merchant_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Cargo Types ----
    cargo_rows = [
        "INSERT OR IGNORE INTO CargoTypes (CargoCode, CargoName, MatterState, StorageUnit) "
        "VALUES ('CRG-001', 'Quantum Dilithium', 'Crystal', 'Kilo-Crates')",
        "INSERT OR IGNORE INTO CargoTypes (CargoCode, CargoName, MatterState, StorageUnit) "
        "VALUES ('CRG-002', 'Hyper-Rations', 'Solid', 'Pallets')",
        "INSERT OR IGNORE INTO CargoTypes (CargoCode, CargoName, MatterState, StorageUnit) "
        "VALUES ('CRG-003', 'Dark Matter Fuel', 'Plasma', 'Containment Casks')",
        "INSERT OR IGNORE INTO CargoTypes (CargoCode, CargoName, MatterState, StorageUnit) "
        "VALUES ('CRG-004', 'Medical Nanobots', 'Liquid', 'Vials')",
        "INSERT OR IGNORE INTO CargoTypes (CargoCode, CargoName, MatterState, StorageUnit) "
        "VALUES ('CRG-005', 'Scrap Metal', 'Solid', 'Tons')",
    ]
    for row in cargo_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Equipment ----
    equipment_rows = [
        "INSERT OR IGNORE INTO Equipment (EquipTag, EquipName, StationId, SectorId, Category, OperationalStatus, CreditValue, CommissionDate) "
        "VALUES ('EQP-001', 'Plasma Emitter Array', 1, 1, 'Weaponry', 'Online', 150000.00, '2145-01-10')",
        "INSERT OR IGNORE INTO Equipment (EquipTag, EquipName, StationId, SectorId, Category, OperationalStatus, CreditValue, CommissionDate) "
        "VALUES ('EQP-002', 'Cryo-Chamber Gen 3', 2, 2, 'LifeSupport', 'Online', 30000.00, '2145-02-15')",
        "INSERT OR IGNORE INTO Equipment (EquipTag, EquipName, StationId, SectorId, Category, OperationalStatus, CreditValue, CommissionDate) "
        "VALUES ('EQP-003', 'Tractor Beam Core', 1, 1, 'Navigation', 'Maintenance', 250000.00, '2144-12-05')",
        "INSERT OR IGNORE INTO Equipment (EquipTag, EquipName, StationId, SectorId, Category, OperationalStatus, CreditValue) "
        "VALUES ('EQP-004', 'Gravity Generator', 3, 3, 'LifeSupport', 'Online', 850000.00)",
        "INSERT OR IGNORE INTO Equipment (EquipTag, EquipName, StationId, SectorId, Category, OperationalStatus, CreditValue) "
        "VALUES ('EQP-005', 'Asteroid Drill', 3, 3, 'Mining', 'Decommissioned', 45000.00)",
        "INSERT OR IGNORE INTO Equipment (EquipTag, EquipName, StationId, SectorId, Category, OperationalStatus, CreditValue) "
        "VALUES ('EQP-006', 'Deflector Shield Emitter', 1, 5, 'Defense', 'Online', 2100000.00)",
        "INSERT OR IGNORE INTO Equipment (EquipTag, EquipName, StationId, SectorId, Category, OperationalStatus, CreditValue) "
        "VALUES ('EQP-007', 'Coolant Pump', 4, 4, 'Infrastructure', 'Maintenance', 12000.00)",
        "INSERT OR IGNORE INTO Equipment (EquipTag, EquipName, StationId, SectorId, Category, OperationalStatus, CreditValue) "
        "VALUES ('EQP-008', 'Hyperspace Relay', 2, 2, 'Comms', 'Online', 550000.00)",
    ]
    for row in equipment_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Trade Agreements ----
    agreement_rows = [
        "INSERT OR IGNORE INTO TradeAgreements (AgreementNumber, CaptainId, AgreementDate, Status, StationId) "
        "VALUES ('TAG-1001', 1, '2146-02-01', 'Fulfilled', 1)",
        "INSERT OR IGNORE INTO TradeAgreements (AgreementNumber, CaptainId, AgreementDate, Status, StationId) "
        "VALUES ('TAG-1002', 2, '2146-02-20', 'Open', 2)",
        "INSERT OR IGNORE INTO TradeAgreements (AgreementNumber, CaptainId, AgreementDate, Status, StationId) "
        "VALUES ('TAG-1003', 3, '2146-03-10', 'Open', 3)",
        "INSERT OR IGNORE INTO TradeAgreements (AgreementNumber, CaptainId, AgreementDate, Status, StationId) "
        "VALUES ('TAG-1004', 4, '2145-12-05', 'Fulfilled', 4)",
    ]
    for row in agreement_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Trade Agreement Lines ----
    agreement_line_rows = [
        "INSERT OR IGNORE INTO TradeAgreementLines (AgreementId, LineSequence, CargoId, CargoCode, MassVolume, CreditPerUnit) "
        "VALUES (1, 1, 1, 'CRG-001', 50.0, 16000.00)",
        "INSERT OR IGNORE INTO TradeAgreementLines (AgreementId, LineSequence, CargoId, CargoCode, MassVolume, CreditPerUnit) "
        "VALUES (2, 1, 2, 'CRG-002', 1000.0, 35.00)",
    ]
    for row in agreement_line_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Invoices ----
    invoice_rows = [
        "INSERT OR IGNORE INTO Invoices (MerchantId, InvoiceNumber, InvoiceCycle, TotalCredits, Status) "
        "VALUES (1, 'INV-2146-01', '2146-01-01', 45000.00, 'Paid')",
        "INSERT OR IGNORE INTO Invoices (MerchantId, InvoiceNumber, InvoiceCycle, TotalCredits, Status) "
        "VALUES (3, 'INV-2146-02', '2146-02-15', 125000.00, 'Pending')",
        "INSERT OR IGNORE INTO Invoices (MerchantId, InvoiceNumber, InvoiceCycle, TotalCredits, Status) "
        "VALUES (4, 'INV-2146-03', '2146-03-01', 890000.00, 'Overdue')",
    ]
    for row in invoice_rows:
        _insert_if_absent(db_cursor, row)

    # ---- Supply Contracts ----
    contract_rows = [
        "INSERT OR IGNORE INTO SupplyContracts (ContractNumber, MerchantId, RatificationDate, Status, StationId) "
        "VALUES ('CON-001', 4, '2145-06-01', 'Active', 3)",
        "INSERT OR IGNORE INTO SupplyContracts (ContractNumber, MerchantId, RatificationDate, Status, StationId) "
        "VALUES ('CON-002', 3, '2144-11-15', 'Terminated', 1)",
    ]
    for row in contract_rows:
        _insert_if_absent(db_cursor, row)


def main():
    """Entry-point: connect, build tables, seed rows, then close."""
    connection = sqlite3.connect(DATABASE_FILE)
    db_cursor = connection.cursor()

    print(f"Opening connection to {DATABASE_FILE} ...")
    initialize_tables(db_cursor)
    print("All tables created.")

    populate_sample_records(db_cursor)
    print("Sample records inserted.")

    connection.commit()
    connection.close()
    print("Database initialization finished.")


if __name__ == '__main__':
    main()
