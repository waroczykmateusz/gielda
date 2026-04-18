CREATE TABLE IF NOT EXISTS positions (
    market        VARCHAR(8)  NOT NULL,
    symbol        VARCHAR(20) NOT NULL,
    nazwa         TEXT        NOT NULL,
    akcje         NUMERIC     NOT NULL,
    srednia_cena  NUMERIC     NOT NULL,
    alert_powyzej NUMERIC,
    alert_ponizej NUMERIC,
    PRIMARY KEY (market, symbol)
);

CREATE TABLE IF NOT EXISTS sent_alerts (
    alert_key  VARCHAR(60) PRIMARY KEY,
    price      NUMERIC     NOT NULL,
    sent_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sent_alerts_expires ON sent_alerts(expires_at);
