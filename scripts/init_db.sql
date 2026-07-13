-- ═══════════════════════════════════════════════════════════════
--  ULRICH — Initialisation de la base de données
-- ═══════════════════════════════════════════════════════════════

-- Extension UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Zones réseau (ex: Bâtiment A, Salle serveur, Etage 2…) ──
CREATE TABLE IF NOT EXISTS zones (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color       VARCHAR(7) DEFAULT '#3B82F6',  -- couleur hex pour la carte
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Équipements découverts ───────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip_address      INET NOT NULL UNIQUE,
    mac_address     MACADDR,
    hostname        VARCHAR(255),
    device_type     VARCHAR(50) DEFAULT 'unknown',
    -- Types: router, switch, server, workstation, printer, ap, unknown
    vendor          VARCHAR(100),
    os_info         VARCHAR(200),
    zone_id         UUID REFERENCES zones(id) ON DELETE SET NULL,
    open_ports      JSONB DEFAULT '[]',
    snmp_community  VARCHAR(100) DEFAULT 'public',
    is_active       BOOLEAN DEFAULT TRUE,
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Résultats de ping / disponibilité ───────────────────────
CREATE TABLE IF NOT EXISTS ping_results (
    id          BIGSERIAL PRIMARY KEY,
    device_id   UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    is_up       BOOLEAN NOT NULL,
    latency_ms  FLOAT,
    checked_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour les requêtes de monitoring (dernières 24h, etc.)
CREATE INDEX IF NOT EXISTS idx_ping_device_time
    ON ping_results (device_id, checked_at DESC);

-- ─── Métriques SNMP (CPU, RAM, trafic) ───────────────────────
CREATE TABLE IF NOT EXISTS snmp_metrics (
    id              BIGSERIAL PRIMARY KEY,
    device_id       UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    cpu_percent     FLOAT,
    ram_percent     FLOAT,
    uptime_seconds  BIGINT,
    if_in_octets    BIGINT,   -- trafic entrant
    if_out_octets   BIGINT,   -- trafic sortant
    raw_data        JSONB DEFAULT '{}',
    collected_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snmp_device_time
    ON snmp_metrics (device_id, collected_at DESC);

-- ─── Incidents / pannes ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS incidents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id       UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    severity        VARCHAR(20) DEFAULT 'warning',
    -- Valeurs: info, warning, critical
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    status          VARCHAR(20) DEFAULT 'open',
    -- Valeurs: open, acknowledged, resolved
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Règles d'alerte ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alert_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    condition_type  VARCHAR(50) NOT NULL,
    -- Types: device_down, high_latency, high_cpu, high_ram
    threshold       FLOAT,
    duration_secs   INT DEFAULT 0,
    notify_email    TEXT[],
    notify_webhook  TEXT[],
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Historique des notifications envoyées ────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id          BIGSERIAL PRIMARY KEY,
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    channel     VARCHAR(20) NOT NULL,  -- email, webhook, sms
    recipient   VARCHAR(255),
    status      VARCHAR(20) DEFAULT 'sent',
    sent_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Utilisateurs ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(100) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(20) DEFAULT 'viewer',
    -- Rôles: admin, technician, viewer
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Données initiales ────────────────────────────────────────
INSERT INTO zones (name, description, color) VALUES
    ('Salle serveurs',  'Datacenter principal',      '#EF4444'),
    ('Réseau bureaux',  'Postes administratifs',     '#3B82F6'),
    ('Wi-Fi',           'Points d''accès sans fil',  '#10B981'),
    ('DMZ',             'Zone démilitarisée',        '#F59E0B')
ON CONFLICT (name) DO NOTHING;

INSERT INTO alert_rules (name, condition_type, threshold, duration_secs, is_active) VALUES
    ('Équipement hors ligne',    'device_down',   NULL,  0,   TRUE),
    ('Latence élevée',           'high_latency',  200.0, 60,  TRUE),
    ('CPU critique',             'high_cpu',      90.0,  120, TRUE),
    ('RAM critique',             'high_ram',      95.0,  120, TRUE)
ON CONFLICT DO NOTHING;

-- Compte admin par défaut (mot de passe: Admin1234! — à changer !)
INSERT INTO users (username, email, hashed_password, role) VALUES
    ('admin', 'admin@ulrich.local',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJP7E3VZi',
     'admin')
ON CONFLICT (username) DO NOTHING;
