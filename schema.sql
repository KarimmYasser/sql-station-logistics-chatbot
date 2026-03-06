-- SQL Server DDL for Space Station Supply Chatbot

CREATE TABLE Captains (
    CaptainId INT IDENTITY PRIMARY KEY,
    CaptainCode VARCHAR(50) UNIQUE NOT NULL,
    CaptainName NVARCHAR(200) NOT NULL,
    CommsChannel NVARCHAR(200) NULL,
    ShipRegistry NVARCHAR(50) NULL,
    HomePlanet NVARCHAR(200) NULL,
    AllianceAffiliation NVARCHAR(100) NULL,
    Rank NVARCHAR(100) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Merchants (
    MerchantId INT IDENTITY PRIMARY KEY,
    MerchantCode VARCHAR(50) UNIQUE NOT NULL,
    MerchantName NVARCHAR(200) NOT NULL,
    CommsChannel NVARCHAR(200) NULL,
    GuildName NVARCHAR(50) NULL,
    PrimaryHub NVARCHAR(200) NULL,
    Sector NVARCHAR(100) NULL,
    System NVARCHAR(100) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Stations (
    StationId INT IDENTITY PRIMARY KEY,
    StationCode VARCHAR(50) UNIQUE NOT NULL,
    StationName NVARCHAR(200) NOT NULL,
    OrbitingBody NVARCHAR(200) NULL,
    System NVARCHAR(100) NULL,
    Galaxy NVARCHAR(100) NULL,
    LocalTimeCycle NVARCHAR(100) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Sectors (
    SectorId INT IDENTITY PRIMARY KEY,
    StationId INT NOT NULL,
    SectorCode VARCHAR(50) NOT NULL,
    SectorName NVARCHAR(200) NOT NULL,
    ParentSectorId INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CONSTRAINT UQ_Sectors_StationCode UNIQUE (StationId, SectorCode),
    CONSTRAINT FK_Sectors_Station FOREIGN KEY (StationId) REFERENCES Stations (StationId),
    CONSTRAINT FK_Sectors_Parent FOREIGN KEY (ParentSectorId) REFERENCES Sectors (SectorId)
);

CREATE TABLE CargoTypes (
    CargoId INT IDENTITY PRIMARY KEY,
    CargoCode NVARCHAR(100) UNIQUE NOT NULL,
    CargoName NVARCHAR(200) NOT NULL,
    MatterState NVARCHAR(100) NULL,
    StorageUnit NVARCHAR(50) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Equipment (
    EquipId INT IDENTITY PRIMARY KEY,
    EquipTag VARCHAR(100) UNIQUE NOT NULL,
    EquipName NVARCHAR(200) NOT NULL,
    StationId INT NOT NULL,
    SectorId INT NULL,
    SerialDesignation NVARCHAR(200) NULL,
    Category NVARCHAR(100) NULL,
    OperationalStatus VARCHAR(30) NOT NULL DEFAULT 'Online',
    CreditValue DECIMAL(18, 2) NULL,
    CommissionDate DATE NULL,
    MerchantId INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT FK_Equipment_Station FOREIGN KEY (StationId) REFERENCES Stations (StationId),
    CONSTRAINT FK_Equipment_Sector FOREIGN KEY (SectorId) REFERENCES Sectors (SectorId),
    CONSTRAINT FK_Equipment_Merchant FOREIGN KEY (MerchantId) REFERENCES Merchants (MerchantId)
);

CREATE TABLE Invoices (
    InvoiceId INT IDENTITY PRIMARY KEY,
    MerchantId INT NOT NULL,
    InvoiceNumber VARCHAR(100) NOT NULL,
    InvoiceCycle DATE NOT NULL,
    CycleEnd DATE NULL,
    TotalCredits DECIMAL(18, 2) NOT NULL,
    Currency VARCHAR(20) NOT NULL DEFAULT 'GalacticCredits',
    Status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT UQ_Invoices_Merchant_InvoiceNumber UNIQUE (MerchantId, InvoiceNumber),
    CONSTRAINT FK_Invoices_Merchant FOREIGN KEY (MerchantId) REFERENCES Merchants (MerchantId)
);

CREATE TABLE SupplyContracts (
    ContractId INT IDENTITY PRIMARY KEY,
    ContractNumber VARCHAR(100) NOT NULL,
    MerchantId INT NOT NULL,
    RatificationDate DATE NOT NULL,
    Status VARCHAR(30) NOT NULL DEFAULT 'Active',
    StationId INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT UQ_SupplyContracts_Number UNIQUE (ContractNumber),
    CONSTRAINT FK_SupplyContracts_Merchant FOREIGN KEY (MerchantId) REFERENCES Merchants (MerchantId),
    CONSTRAINT FK_SupplyContracts_Station FOREIGN KEY (StationId) REFERENCES Stations (StationId)
);

CREATE TABLE SupplyContractLines (
    LineId INT IDENTITY PRIMARY KEY,
    ContractId INT NOT NULL,
    LineSequence INT NOT NULL,
    CargoId INT NULL,
    CargoCode NVARCHAR(100) NOT NULL,
    ManifestDetails NVARCHAR(200) NULL,
    MassVolume DECIMAL(18, 4) NOT NULL,
    CreditPerUnit DECIMAL(18, 4) NOT NULL,
    CONSTRAINT UQ_SupplyContractLines UNIQUE (ContractId, LineSequence),
    CONSTRAINT FK_SupplyContractLines_Contract FOREIGN KEY (ContractId) REFERENCES SupplyContracts (ContractId),
    CONSTRAINT FK_SupplyContractLines_Cargo FOREIGN KEY (CargoId) REFERENCES CargoTypes (CargoId)
);

CREATE TABLE TradeAgreements (
    AgreementId INT IDENTITY PRIMARY KEY,
    AgreementNumber VARCHAR(100) NOT NULL,
    CaptainId INT NOT NULL,
    AgreementDate DATE NOT NULL,
    Status VARCHAR(30) NOT NULL DEFAULT 'Open',
    StationId INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT UQ_TradeAgreements_Number UNIQUE (AgreementNumber),
    CONSTRAINT FK_TradeAgreements_Captain FOREIGN KEY (CaptainId) REFERENCES Captains (CaptainId),
    CONSTRAINT FK_TradeAgreements_Station FOREIGN KEY (StationId) REFERENCES Stations (StationId)
);

CREATE TABLE TradeAgreementLines (
    AgreementLineId INT IDENTITY PRIMARY KEY,
    AgreementId INT NOT NULL,
    LineSequence INT NOT NULL,
    CargoId INT NULL,
    CargoCode NVARCHAR(100) NOT NULL,
    ManifestDetails NVARCHAR(200) NULL,
    MassVolume DECIMAL(18, 4) NOT NULL,
    CreditPerUnit DECIMAL(18, 4) NOT NULL,
    CONSTRAINT UQ_TradeAgreementLines UNIQUE (AgreementId, LineSequence),
    CONSTRAINT FK_TradeAgreementLines_Agreement FOREIGN KEY (AgreementId) REFERENCES TradeAgreements (AgreementId),
    CONSTRAINT FK_TradeAgreementLines_Cargo FOREIGN KEY (CargoId) REFERENCES CargoTypes (CargoId)
);

CREATE TABLE EquipmentTransfers (
    TransferId INT IDENTITY PRIMARY KEY,
    EquipId INT NOT NULL,
    FromSectorId INT NULL,
    ToSectorId INT NULL,
    TransferType VARCHAR(30) NOT NULL,
    UnitCount INT NOT NULL DEFAULT 1,
    TransferCycle DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME (),
    LogEntry NVARCHAR(500) NULL,
    CONSTRAINT FK_EquipmentTransfers_Equipment FOREIGN KEY (EquipId) REFERENCES Equipment (EquipId),
    CONSTRAINT FK_EquipmentTransfers_FromSector FOREIGN KEY (FromSectorId) REFERENCES Sectors (SectorId),
    CONSTRAINT FK_EquipmentTransfers_ToSector FOREIGN KEY (ToSectorId) REFERENCES Sectors (SectorId)
);