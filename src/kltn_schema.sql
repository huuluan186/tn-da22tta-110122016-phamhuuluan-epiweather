--
-- PostgreSQL database dump
--

\restrict Cbmx4yIaPvyQsd3caJ2h7yUDyCsPzRystXesbPsIopEpRmgmR9IyelaC4H2ROxf

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: api_request_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_request_logs (
    id bigint NOT NULL,
    endpoint character varying(100),
    method character varying(10),
    disease character varying(20),
    iso3 character(3),
    iso_year smallint,
    iso_week smallint,
    model_version_id integer,
    response_ms integer,
    status_code smallint,
    requested_at timestamp with time zone DEFAULT now() NOT NULL
)
PARTITION BY RANGE (requested_at);


--
-- Name: api_request_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.api_request_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: api_request_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.api_request_logs_id_seq OWNED BY public.api_request_logs.id;


--
-- Name: api_logs_2026; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_logs_2026 (
    id bigint DEFAULT nextval('public.api_request_logs_id_seq'::regclass) CONSTRAINT api_request_logs_id_not_null NOT NULL,
    endpoint character varying(100),
    method character varying(10),
    disease character varying(20),
    iso3 character(3),
    iso_year smallint,
    iso_week smallint,
    model_version_id integer,
    response_ms integer,
    status_code smallint,
    requested_at timestamp with time zone DEFAULT now() CONSTRAINT api_request_logs_requested_at_not_null NOT NULL
);


--
-- Name: api_logs_default; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_logs_default (
    id bigint DEFAULT nextval('public.api_request_logs_id_seq'::regclass) CONSTRAINT api_request_logs_id_not_null NOT NULL,
    endpoint character varying(100),
    method character varying(10),
    disease character varying(20),
    iso3 character(3),
    iso_year smallint,
    iso_week smallint,
    model_version_id integer,
    response_ms integer,
    status_code smallint,
    requested_at timestamp with time zone DEFAULT now() CONSTRAINT api_request_logs_requested_at_not_null NOT NULL
);


--
-- Name: countries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.countries (
    iso3 character(3) NOT NULL,
    iso2 character(2),
    country_name character varying(100) NOT NULL,
    who_region character varying(10),
    who_region_enc smallint,
    latitude double precision,
    longitude double precision,
    population bigint,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: data_quality_checks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_quality_checks (
    id integer NOT NULL,
    run_id uuid,
    check_name character varying(100) NOT NULL,
    table_name character varying(50),
    iso_year smallint,
    iso_week smallint,
    threshold double precision,
    actual_value double precision,
    passed boolean NOT NULL,
    detail text,
    checked_at timestamp with time zone DEFAULT now()
);


--
-- Name: data_quality_checks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_quality_checks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: data_quality_checks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_quality_checks_id_seq OWNED BY public.data_quality_checks.id;


--
-- Name: data_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_sources (
    id integer NOT NULL,
    code character varying(30) NOT NULL,
    source_type character varying(20) NOT NULL,
    url text,
    update_frequency character varying(20),
    spatial_coverage character varying(50),
    temporal_start date,
    is_active boolean DEFAULT true,
    description text,
    CONSTRAINT data_sources_source_type_check CHECK (((source_type)::text = ANY ((ARRAY['disease'::character varying, 'weather'::character varying, 'socioeconomic'::character varying])::text[])))
);


--
-- Name: data_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: data_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_sources_id_seq OWNED BY public.data_sources.id;


--
-- Name: disease_cases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases (
    id bigint NOT NULL,
    disease_id integer NOT NULL,
    iso3 character(3) NOT NULL,
    source_id integer,
    iso_year smallint NOT NULL,
    iso_week smallint NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
)
PARTITION BY RANGE (iso_year);


--
-- Name: disease_cases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.disease_cases_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: disease_cases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.disease_cases_id_seq OWNED BY public.disease_cases.id;


--
-- Name: disease_cases_2010; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2010 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2011; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2011 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2012; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2012 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2013; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2013 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2014; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2014 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2015; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2015 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2016; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2016 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2017; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2017 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2018; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2018 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2019; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2019 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2020; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2020 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2021; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2021 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_2022; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_2022 (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: disease_cases_default; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.disease_cases_default (
    id bigint DEFAULT nextval('public.disease_cases_id_seq'::regclass) CONSTRAINT disease_cases_id_not_null NOT NULL,
    disease_id integer CONSTRAINT disease_cases_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT disease_cases_iso3_not_null NOT NULL,
    source_id integer,
    iso_year smallint CONSTRAINT disease_cases_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT disease_cases_iso_week_not_null NOT NULL,
    raw_count integer,
    transformed_value double precision,
    data_quality smallint DEFAULT 1,
    ingested_at timestamp with time zone DEFAULT now(),
    CONSTRAINT disease_cases_data_quality_check CHECK ((data_quality = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: diseases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.diseases (
    id integer NOT NULL,
    code character varying(20) NOT NULL,
    display_name character varying(100) NOT NULL,
    target_variable character varying(50) NOT NULL,
    target_transform character varying(20) DEFAULT 'log1p'::character varying,
    is_active boolean DEFAULT true,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    display_name_vi character varying(100),
    description_vi text,
    CONSTRAINT diseases_target_transform_check CHECK (((target_transform)::text = ANY ((ARRAY['log1p'::character varying, 'none'::character varying, 'sqrt'::character varying])::text[])))
);


--
-- Name: diseases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.diseases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: diseases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.diseases_id_seq OWNED BY public.diseases.id;


--
-- Name: feature_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feature_configs (
    id integer NOT NULL,
    disease_id integer NOT NULL,
    feature_name character varying(100) NOT NULL,
    source_type character varying(20) NOT NULL,
    weather_variable character varying(50),
    lag_weeks smallint DEFAULT 0,
    transform character varying(20) DEFAULT 'none'::character varying,
    ar_target character varying(50),
    ar_lag_weeks smallint,
    is_active boolean DEFAULT true,
    version_tag character varying(30),
    display_name_vi character varying(150),
    description_vi character varying(500),
    CONSTRAINT feature_configs_source_type_check CHECK (((source_type)::text = ANY ((ARRAY['weather'::character varying, 'ar_lag'::character varying, 'geographic'::character varying, 'socioeconomic'::character varying, 'calendar'::character varying])::text[])))
);


--
-- Name: feature_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.feature_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: feature_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feature_configs_id_seq OWNED BY public.feature_configs.id;


--
-- Name: feature_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feature_snapshots (
    disease_id integer NOT NULL,
    iso3 character(3) NOT NULL,
    iso_year smallint NOT NULL,
    iso_week smallint NOT NULL,
    features jsonb NOT NULL,
    feature_version character varying(10) DEFAULT 'v1'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE feature_snapshots; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.feature_snapshots IS 'Pre-computed feature vectors cho ML inference. JSONB cho phÃ©p má»Ÿ rá»™ng feature set khÃ´ng cáº§n ALTER TABLE.';


--
-- Name: COLUMN feature_snapshots.features; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_snapshots.features IS 'JSON dict: feature_name -> float. VÃ­ dá»¥ {"flu_log_lag1": 4.5, "temp_c_lag3": 25.6, ...}';


--
-- Name: model_evaluations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_evaluations (
    id integer NOT NULL,
    model_version_id integer NOT NULL,
    eval_set character varying(30) NOT NULL,
    eval_type character varying(20) NOT NULL,
    r2_score double precision,
    mae double precision,
    rmse double precision,
    smape_nonzero double precision,
    risk_macro_f1 double precision,
    risk_accuracy double precision,
    risk_low_f1 double precision,
    risk_medium_f1 double precision,
    risk_high_f1 double precision,
    n_samples integer,
    notes text,
    evaluated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT model_evaluations_eval_type_check CHECK (((eval_type)::text = ANY ((ARRAY['holdout'::character varying, 'cv'::character varying, 'production_drift'::character varying])::text[])))
);


--
-- Name: model_evaluations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_evaluations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_evaluations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_evaluations_id_seq OWNED BY public.model_evaluations.id;


--
-- Name: model_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_versions (
    id integer NOT NULL,
    disease_id integer NOT NULL,
    version character varying(30) NOT NULL,
    algorithm character varying(30) DEFAULT 'XGBoost'::character varying,
    description text,
    train_year_start smallint NOT NULL,
    train_year_end smallint NOT NULL,
    val_year smallint,
    feature_config_tag character varying(30),
    hyperparams jsonb,
    artifact_path character varying(255),
    is_active boolean DEFAULT false,
    is_champion boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: model_versions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_versions_id_seq OWNED BY public.model_versions.id;


--
-- Name: predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.predictions (
    id bigint NOT NULL,
    disease_id integer NOT NULL,
    iso3 character(3) NOT NULL,
    iso_year smallint NOT NULL,
    iso_week smallint NOT NULL,
    horizon_weeks smallint DEFAULT 1,
    predicted_value double precision,
    predicted_cases double precision,
    risk_level character varying(10),
    model_version_id integer,
    features_snapshot jsonb,
    confidence_lo double precision,
    confidence_hi double precision,
    created_at timestamp with time zone DEFAULT now(),
    risk_probability double precision,
    CONSTRAINT predictions_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['Low'::character varying, 'Medium'::character varying, 'High'::character varying])::text[])))
)
PARTITION BY RANGE (iso_year);


--
-- Name: mv_latest_predictions; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_latest_predictions AS
 SELECT DISTINCT ON (p.disease_id, p.iso3, p.horizon_weeks) p.disease_id,
    d.code AS disease_code,
    p.iso3,
    c.country_name,
    c.who_region,
    p.iso_year,
    p.iso_week,
    p.horizon_weeks,
    p.predicted_cases,
    p.risk_level,
    p.created_at
   FROM ((public.predictions p
     JOIN public.diseases d ON ((d.id = p.disease_id)))
     JOIN public.countries c ON ((c.iso3 = p.iso3)))
  ORDER BY p.disease_id, p.iso3, p.horizon_weeks, p.created_at DESC
  WITH NO DATA;


--
-- Name: pipeline_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pipeline_runs (
    run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    pipeline_name character varying(50) NOT NULL,
    pipeline_version character varying(20),
    trigger_type character varying(20) DEFAULT 'manual'::character varying,
    status character varying(20) NOT NULL,
    iso_year smallint,
    iso_week smallint,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    duration_sec double precision GENERATED ALWAYS AS (EXTRACT(epoch FROM (completed_at - started_at))) STORED,
    rows_processed integer,
    rows_inserted integer,
    rows_updated integer,
    rows_skipped integer,
    errors jsonb,
    metadata jsonb,
    CONSTRAINT pipeline_runs_status_check CHECK (((status)::text = ANY ((ARRAY['queued'::character varying, 'running'::character varying, 'success'::character varying, 'failed'::character varying, 'partial'::character varying])::text[]))),
    CONSTRAINT pipeline_runs_trigger_type_check CHECK (((trigger_type)::text = ANY ((ARRAY['manual'::character varying, 'scheduled'::character varying, 'api'::character varying, 'event'::character varying])::text[])))
);


--
-- Name: predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.predictions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.predictions_id_seq OWNED BY public.predictions.id;


--
-- Name: predictions_2022; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.predictions_2022 (
    id bigint DEFAULT nextval('public.predictions_id_seq'::regclass) CONSTRAINT predictions_id_not_null NOT NULL,
    disease_id integer CONSTRAINT predictions_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT predictions_iso3_not_null NOT NULL,
    iso_year smallint CONSTRAINT predictions_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT predictions_iso_week_not_null NOT NULL,
    horizon_weeks smallint DEFAULT 1,
    predicted_value double precision,
    predicted_cases double precision,
    risk_level character varying(10),
    model_version_id integer,
    features_snapshot jsonb,
    confidence_lo double precision,
    confidence_hi double precision,
    created_at timestamp with time zone DEFAULT now(),
    risk_probability double precision,
    CONSTRAINT predictions_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['Low'::character varying, 'Medium'::character varying, 'High'::character varying])::text[])))
);


--
-- Name: predictions_2023; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.predictions_2023 (
    id bigint DEFAULT nextval('public.predictions_id_seq'::regclass) CONSTRAINT predictions_id_not_null NOT NULL,
    disease_id integer CONSTRAINT predictions_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT predictions_iso3_not_null NOT NULL,
    iso_year smallint CONSTRAINT predictions_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT predictions_iso_week_not_null NOT NULL,
    horizon_weeks smallint DEFAULT 1,
    predicted_value double precision,
    predicted_cases double precision,
    risk_level character varying(10),
    model_version_id integer,
    features_snapshot jsonb,
    confidence_lo double precision,
    confidence_hi double precision,
    created_at timestamp with time zone DEFAULT now(),
    risk_probability double precision,
    CONSTRAINT predictions_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['Low'::character varying, 'Medium'::character varying, 'High'::character varying])::text[])))
);


--
-- Name: predictions_default; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.predictions_default (
    id bigint DEFAULT nextval('public.predictions_id_seq'::regclass) CONSTRAINT predictions_id_not_null NOT NULL,
    disease_id integer CONSTRAINT predictions_disease_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT predictions_iso3_not_null NOT NULL,
    iso_year smallint CONSTRAINT predictions_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT predictions_iso_week_not_null NOT NULL,
    horizon_weeks smallint DEFAULT 1,
    predicted_value double precision,
    predicted_cases double precision,
    risk_level character varying(10),
    model_version_id integer,
    features_snapshot jsonb,
    confidence_lo double precision,
    confidence_hi double precision,
    created_at timestamp with time zone DEFAULT now(),
    risk_probability double precision,
    CONSTRAINT predictions_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['Low'::character varying, 'Medium'::character varying, 'High'::character varying])::text[])))
);


--
-- Name: weather_observations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_observations (
    id bigint NOT NULL,
    iso3 character(3) NOT NULL,
    source_id integer NOT NULL,
    iso_year smallint NOT NULL,
    iso_week smallint NOT NULL,
    data jsonb NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
)
PARTITION BY RANGE (iso_year);


--
-- Name: weather_observations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weather_observations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weather_observations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weather_observations_id_seq OWNED BY public.weather_observations.id;


--
-- Name: weather_obs_2010; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2010 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2011; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2011 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2012; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2012 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2013; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2013 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2014; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2014 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2015; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2015 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2016; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2016 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2017; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2017 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2018; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2018 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2019; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2019 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_2022; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_2022 (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_obs_default; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_obs_default (
    id bigint DEFAULT nextval('public.weather_observations_id_seq'::regclass) CONSTRAINT weather_observations_id_not_null NOT NULL,
    iso3 character(3) CONSTRAINT weather_observations_iso3_not_null NOT NULL,
    source_id integer CONSTRAINT weather_observations_source_id_not_null NOT NULL,
    iso_year smallint CONSTRAINT weather_observations_iso_year_not_null NOT NULL,
    iso_week smallint CONSTRAINT weather_observations_iso_week_not_null NOT NULL,
    data jsonb CONSTRAINT weather_observations_data_not_null NOT NULL,
    ingested_at timestamp with time zone DEFAULT now()
);


--
-- Name: weather_variables; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weather_variables (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    display_name character varying(100),
    unit character varying(20),
    source_id integer,
    era5_variable character varying(100),
    description text,
    is_active boolean DEFAULT true
);


--
-- Name: weather_variables_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weather_variables_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weather_variables_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weather_variables_id_seq OWNED BY public.weather_variables.id;


--
-- Name: api_logs_2026; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_request_logs ATTACH PARTITION public.api_logs_2026 FOR VALUES FROM ('2026-01-01 00:00:00+07') TO ('2027-01-01 00:00:00+07');


--
-- Name: api_logs_default; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_request_logs ATTACH PARTITION public.api_logs_default DEFAULT;


--
-- Name: disease_cases_2010; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2010 FOR VALUES FROM ('2010') TO ('2011');


--
-- Name: disease_cases_2011; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2011 FOR VALUES FROM ('2011') TO ('2012');


--
-- Name: disease_cases_2012; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2012 FOR VALUES FROM ('2012') TO ('2013');


--
-- Name: disease_cases_2013; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2013 FOR VALUES FROM ('2013') TO ('2014');


--
-- Name: disease_cases_2014; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2014 FOR VALUES FROM ('2014') TO ('2015');


--
-- Name: disease_cases_2015; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2015 FOR VALUES FROM ('2015') TO ('2016');


--
-- Name: disease_cases_2016; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2016 FOR VALUES FROM ('2016') TO ('2017');


--
-- Name: disease_cases_2017; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2017 FOR VALUES FROM ('2017') TO ('2018');


--
-- Name: disease_cases_2018; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2018 FOR VALUES FROM ('2018') TO ('2019');


--
-- Name: disease_cases_2019; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2019 FOR VALUES FROM ('2019') TO ('2020');


--
-- Name: disease_cases_2020; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2020 FOR VALUES FROM ('2020') TO ('2021');


--
-- Name: disease_cases_2021; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2021 FOR VALUES FROM ('2021') TO ('2022');


--
-- Name: disease_cases_2022; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_2022 FOR VALUES FROM ('2022') TO ('2023');


--
-- Name: disease_cases_default; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ATTACH PARTITION public.disease_cases_default DEFAULT;


--
-- Name: predictions_2022; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions ATTACH PARTITION public.predictions_2022 FOR VALUES FROM ('2022') TO ('2023');


--
-- Name: predictions_2023; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions ATTACH PARTITION public.predictions_2023 FOR VALUES FROM ('2023') TO ('2024');


--
-- Name: predictions_default; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions ATTACH PARTITION public.predictions_default DEFAULT;


--
-- Name: weather_obs_2010; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2010 FOR VALUES FROM ('2010') TO ('2011');


--
-- Name: weather_obs_2011; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2011 FOR VALUES FROM ('2011') TO ('2012');


--
-- Name: weather_obs_2012; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2012 FOR VALUES FROM ('2012') TO ('2013');


--
-- Name: weather_obs_2013; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2013 FOR VALUES FROM ('2013') TO ('2014');


--
-- Name: weather_obs_2014; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2014 FOR VALUES FROM ('2014') TO ('2015');


--
-- Name: weather_obs_2015; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2015 FOR VALUES FROM ('2015') TO ('2016');


--
-- Name: weather_obs_2016; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2016 FOR VALUES FROM ('2016') TO ('2017');


--
-- Name: weather_obs_2017; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2017 FOR VALUES FROM ('2017') TO ('2018');


--
-- Name: weather_obs_2018; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2018 FOR VALUES FROM ('2018') TO ('2019');


--
-- Name: weather_obs_2019; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2019 FOR VALUES FROM ('2019') TO ('2020');


--
-- Name: weather_obs_2022; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_2022 FOR VALUES FROM ('2022') TO ('2023');


--
-- Name: weather_obs_default; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ATTACH PARTITION public.weather_obs_default DEFAULT;


--
-- Name: api_request_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_request_logs ALTER COLUMN id SET DEFAULT nextval('public.api_request_logs_id_seq'::regclass);


--
-- Name: data_quality_checks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_checks ALTER COLUMN id SET DEFAULT nextval('public.data_quality_checks_id_seq'::regclass);


--
-- Name: data_sources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_sources ALTER COLUMN id SET DEFAULT nextval('public.data_sources_id_seq'::regclass);


--
-- Name: disease_cases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases ALTER COLUMN id SET DEFAULT nextval('public.disease_cases_id_seq'::regclass);


--
-- Name: diseases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diseases ALTER COLUMN id SET DEFAULT nextval('public.diseases_id_seq'::regclass);


--
-- Name: feature_configs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_configs ALTER COLUMN id SET DEFAULT nextval('public.feature_configs_id_seq'::regclass);


--
-- Name: model_evaluations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_evaluations ALTER COLUMN id SET DEFAULT nextval('public.model_evaluations_id_seq'::regclass);


--
-- Name: model_versions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_versions ALTER COLUMN id SET DEFAULT nextval('public.model_versions_id_seq'::regclass);


--
-- Name: predictions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions ALTER COLUMN id SET DEFAULT nextval('public.predictions_id_seq'::regclass);


--
-- Name: weather_observations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations ALTER COLUMN id SET DEFAULT nextval('public.weather_observations_id_seq'::regclass);


--
-- Name: weather_variables id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_variables ALTER COLUMN id SET DEFAULT nextval('public.weather_variables_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_request_logs api_request_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_request_logs
    ADD CONSTRAINT api_request_logs_pkey PRIMARY KEY (id, requested_at);


--
-- Name: api_logs_2026 api_logs_2026_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_logs_2026
    ADD CONSTRAINT api_logs_2026_pkey PRIMARY KEY (id, requested_at);


--
-- Name: api_logs_default api_logs_default_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_logs_default
    ADD CONSTRAINT api_logs_default_pkey PRIMARY KEY (id, requested_at);


--
-- Name: countries countries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_pkey PRIMARY KEY (iso3);


--
-- Name: data_quality_checks data_quality_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_checks
    ADD CONSTRAINT data_quality_checks_pkey PRIMARY KEY (id);


--
-- Name: data_sources data_sources_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_sources
    ADD CONSTRAINT data_sources_code_key UNIQUE (code);


--
-- Name: data_sources data_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_sources
    ADD CONSTRAINT data_sources_pkey PRIMARY KEY (id);


--
-- Name: disease_cases disease_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases
    ADD CONSTRAINT disease_cases_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2010 disease_cases_2010_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2010
    ADD CONSTRAINT disease_cases_2010_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2011 disease_cases_2011_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2011
    ADD CONSTRAINT disease_cases_2011_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2012 disease_cases_2012_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2012
    ADD CONSTRAINT disease_cases_2012_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2013 disease_cases_2013_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2013
    ADD CONSTRAINT disease_cases_2013_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2014 disease_cases_2014_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2014
    ADD CONSTRAINT disease_cases_2014_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2015 disease_cases_2015_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2015
    ADD CONSTRAINT disease_cases_2015_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2016 disease_cases_2016_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2016
    ADD CONSTRAINT disease_cases_2016_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2017 disease_cases_2017_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2017
    ADD CONSTRAINT disease_cases_2017_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2018 disease_cases_2018_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2018
    ADD CONSTRAINT disease_cases_2018_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2019 disease_cases_2019_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2019
    ADD CONSTRAINT disease_cases_2019_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2020 disease_cases_2020_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2020
    ADD CONSTRAINT disease_cases_2020_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2021 disease_cases_2021_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2021
    ADD CONSTRAINT disease_cases_2021_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_2022 disease_cases_2022_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_2022
    ADD CONSTRAINT disease_cases_2022_pkey PRIMARY KEY (id, iso_year);


--
-- Name: disease_cases_default disease_cases_default_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.disease_cases_default
    ADD CONSTRAINT disease_cases_default_pkey PRIMARY KEY (id, iso_year);


--
-- Name: diseases diseases_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diseases
    ADD CONSTRAINT diseases_code_key UNIQUE (code);


--
-- Name: diseases diseases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.diseases
    ADD CONSTRAINT diseases_pkey PRIMARY KEY (id);


--
-- Name: feature_configs feature_configs_disease_id_feature_name_version_tag_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_configs
    ADD CONSTRAINT feature_configs_disease_id_feature_name_version_tag_key UNIQUE (disease_id, feature_name, version_tag);


--
-- Name: feature_configs feature_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_configs
    ADD CONSTRAINT feature_configs_pkey PRIMARY KEY (id);


--
-- Name: feature_snapshots feature_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_snapshots
    ADD CONSTRAINT feature_snapshots_pkey PRIMARY KEY (disease_id, iso3, iso_year, iso_week, feature_version);


--
-- Name: model_evaluations model_evaluations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_evaluations
    ADD CONSTRAINT model_evaluations_pkey PRIMARY KEY (id);


--
-- Name: model_versions model_versions_disease_id_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_versions
    ADD CONSTRAINT model_versions_disease_id_version_key UNIQUE (disease_id, version);


--
-- Name: model_versions model_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_versions
    ADD CONSTRAINT model_versions_pkey PRIMARY KEY (id);


--
-- Name: pipeline_runs pipeline_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pipeline_runs
    ADD CONSTRAINT pipeline_runs_pkey PRIMARY KEY (run_id);


--
-- Name: predictions predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (id, iso_year);


--
-- Name: predictions_2022 predictions_2022_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions_2022
    ADD CONSTRAINT predictions_2022_pkey PRIMARY KEY (id, iso_year);


--
-- Name: predictions_2023 predictions_2023_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions_2023
    ADD CONSTRAINT predictions_2023_pkey PRIMARY KEY (id, iso_year);


--
-- Name: predictions_default predictions_default_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions_default
    ADD CONSTRAINT predictions_default_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_observations weather_observations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_observations
    ADD CONSTRAINT weather_observations_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2010 weather_obs_2010_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2010
    ADD CONSTRAINT weather_obs_2010_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2011 weather_obs_2011_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2011
    ADD CONSTRAINT weather_obs_2011_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2012 weather_obs_2012_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2012
    ADD CONSTRAINT weather_obs_2012_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2013 weather_obs_2013_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2013
    ADD CONSTRAINT weather_obs_2013_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2014 weather_obs_2014_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2014
    ADD CONSTRAINT weather_obs_2014_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2015 weather_obs_2015_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2015
    ADD CONSTRAINT weather_obs_2015_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2016 weather_obs_2016_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2016
    ADD CONSTRAINT weather_obs_2016_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2017 weather_obs_2017_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2017
    ADD CONSTRAINT weather_obs_2017_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2018 weather_obs_2018_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2018
    ADD CONSTRAINT weather_obs_2018_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2019 weather_obs_2019_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2019
    ADD CONSTRAINT weather_obs_2019_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_2022 weather_obs_2022_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_2022
    ADD CONSTRAINT weather_obs_2022_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_obs_default weather_obs_default_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_obs_default
    ADD CONSTRAINT weather_obs_default_pkey PRIMARY KEY (id, iso_year);


--
-- Name: weather_variables weather_variables_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_variables
    ADD CONSTRAINT weather_variables_code_key UNIQUE (code);


--
-- Name: weather_variables weather_variables_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_variables
    ADD CONSTRAINT weather_variables_pkey PRIMARY KEY (id);


--
-- Name: idx_disease_cases_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_disease_cases_unique ON ONLY public.disease_cases USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2010_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2010_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2010 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: idx_disease_cases_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_disease_cases_lookup ON ONLY public.disease_cases USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2010_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2010_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2010 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2011_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2011_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2011 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2011_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2011_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2011 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2012_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2012_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2012 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2012_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2012_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2012 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2013_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2013_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2013 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2013_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2013_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2013 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2014_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2014_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2014 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2014_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2014_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2014 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2015_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2015_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2015 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2015_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2015_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2015 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2016_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2016_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2016 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2016_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2016_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2016 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2017_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2017_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2017 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2017_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2017_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2017 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2018_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2018_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2018 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2018_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2018_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2018 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2019_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2019_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2019 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2019_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2019_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2019 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2020_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2020_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2020 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2020_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2020_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2020 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2021_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2021_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2021 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2021_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2021_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2021 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_2022_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_2022_disease_id_iso3_iso_year_iso_week_source_idx ON public.disease_cases_2022 USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_2022_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_2022_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_2022 USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: disease_cases_default_disease_id_iso3_iso_year_iso_week_sou_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX disease_cases_default_disease_id_iso3_iso_year_iso_week_sou_idx ON public.disease_cases_default USING btree (disease_id, iso3, iso_year, iso_week, source_id);


--
-- Name: disease_cases_default_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX disease_cases_default_iso3_disease_id_iso_year_iso_week_idx ON public.disease_cases_default USING btree (iso3, disease_id, iso_year, iso_week);


--
-- Name: idx_feature_snapshots_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feature_snapshots_country ON public.feature_snapshots USING btree (disease_id, iso3, iso_year, iso_week);


--
-- Name: idx_feature_snapshots_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feature_snapshots_lookup ON public.feature_snapshots USING btree (disease_id, iso_year, iso_week);


--
-- Name: idx_mv_latest; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_mv_latest ON public.mv_latest_predictions USING btree (disease_id, iso3, horizon_weeks);


--
-- Name: idx_pipeline_runs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pipeline_runs_status ON public.pipeline_runs USING btree (pipeline_name, status, started_at DESC);


--
-- Name: idx_predictions_dashboard; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_predictions_dashboard ON ONLY public.predictions USING btree (disease_id, iso_year, iso_week, risk_level);


--
-- Name: idx_predictions_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_predictions_unique ON ONLY public.predictions USING btree (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id);


--
-- Name: idx_weather_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_weather_data_gin ON ONLY public.weather_observations USING gin (data);


--
-- Name: idx_weather_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_weather_unique ON ONLY public.weather_observations USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: predictions_2022_disease_id_iso3_iso_year_iso_week_horizon__idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX predictions_2022_disease_id_iso3_iso_year_iso_week_horizon__idx ON public.predictions_2022 USING btree (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id);


--
-- Name: predictions_2022_disease_id_iso_year_iso_week_risk_level_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX predictions_2022_disease_id_iso_year_iso_week_risk_level_idx ON public.predictions_2022 USING btree (disease_id, iso_year, iso_week, risk_level);


--
-- Name: predictions_2023_disease_id_iso3_iso_year_iso_week_horizon__idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX predictions_2023_disease_id_iso3_iso_year_iso_week_horizon__idx ON public.predictions_2023 USING btree (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id);


--
-- Name: predictions_2023_disease_id_iso_year_iso_week_risk_level_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX predictions_2023_disease_id_iso_year_iso_week_risk_level_idx ON public.predictions_2023 USING btree (disease_id, iso_year, iso_week, risk_level);


--
-- Name: predictions_default_disease_id_iso3_iso_year_iso_week_horiz_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX predictions_default_disease_id_iso3_iso_year_iso_week_horiz_idx ON public.predictions_default USING btree (disease_id, iso3, iso_year, iso_week, horizon_weeks, model_version_id);


--
-- Name: predictions_default_disease_id_iso_year_iso_week_risk_level_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX predictions_default_disease_id_iso_year_iso_week_risk_level_idx ON public.predictions_default USING btree (disease_id, iso_year, iso_week, risk_level);


--
-- Name: weather_obs_2010_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2010_data_idx ON public.weather_obs_2010 USING gin (data);


--
-- Name: weather_obs_2010_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2010_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2010 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2011_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2011_data_idx ON public.weather_obs_2011 USING gin (data);


--
-- Name: weather_obs_2011_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2011_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2011 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2012_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2012_data_idx ON public.weather_obs_2012 USING gin (data);


--
-- Name: weather_obs_2012_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2012_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2012 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2013_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2013_data_idx ON public.weather_obs_2013 USING gin (data);


--
-- Name: weather_obs_2013_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2013_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2013 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2014_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2014_data_idx ON public.weather_obs_2014 USING gin (data);


--
-- Name: weather_obs_2014_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2014_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2014 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2015_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2015_data_idx ON public.weather_obs_2015 USING gin (data);


--
-- Name: weather_obs_2015_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2015_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2015 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2016_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2016_data_idx ON public.weather_obs_2016 USING gin (data);


--
-- Name: weather_obs_2016_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2016_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2016 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2017_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2017_data_idx ON public.weather_obs_2017 USING gin (data);


--
-- Name: weather_obs_2017_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2017_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2017 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2018_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2018_data_idx ON public.weather_obs_2018 USING gin (data);


--
-- Name: weather_obs_2018_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2018_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2018 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2019_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2019_data_idx ON public.weather_obs_2019 USING gin (data);


--
-- Name: weather_obs_2019_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2019_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2019 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_2022_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_2022_data_idx ON public.weather_obs_2022 USING gin (data);


--
-- Name: weather_obs_2022_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_2022_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_2022 USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: weather_obs_default_data_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX weather_obs_default_data_idx ON public.weather_obs_default USING gin (data);


--
-- Name: weather_obs_default_iso3_source_id_iso_year_iso_week_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX weather_obs_default_iso3_source_id_iso_year_iso_week_idx ON public.weather_obs_default USING btree (iso3, source_id, iso_year, iso_week);


--
-- Name: api_logs_2026_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.api_request_logs_pkey ATTACH PARTITION public.api_logs_2026_pkey;


--
-- Name: api_logs_default_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.api_request_logs_pkey ATTACH PARTITION public.api_logs_default_pkey;


--
-- Name: disease_cases_2010_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2010_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2010_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2010_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2010_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2010_pkey;


--
-- Name: disease_cases_2011_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2011_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2011_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2011_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2011_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2011_pkey;


--
-- Name: disease_cases_2012_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2012_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2012_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2012_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2012_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2012_pkey;


--
-- Name: disease_cases_2013_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2013_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2013_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2013_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2013_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2013_pkey;


--
-- Name: disease_cases_2014_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2014_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2014_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2014_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2014_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2014_pkey;


--
-- Name: disease_cases_2015_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2015_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2015_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2015_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2015_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2015_pkey;


--
-- Name: disease_cases_2016_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2016_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2016_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2016_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2016_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2016_pkey;


--
-- Name: disease_cases_2017_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2017_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2017_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2017_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2017_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2017_pkey;


--
-- Name: disease_cases_2018_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2018_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2018_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2018_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2018_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2018_pkey;


--
-- Name: disease_cases_2019_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2019_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2019_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2019_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2019_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2019_pkey;


--
-- Name: disease_cases_2020_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2020_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2020_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2020_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2020_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2020_pkey;


--
-- Name: disease_cases_2021_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2021_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2021_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2021_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2021_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2021_pkey;


--
-- Name: disease_cases_2022_disease_id_iso3_iso_year_iso_week_source_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_2022_disease_id_iso3_iso_year_iso_week_source_idx;


--
-- Name: disease_cases_2022_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_2022_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_2022_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_2022_pkey;


--
-- Name: disease_cases_default_disease_id_iso3_iso_year_iso_week_sou_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_unique ATTACH PARTITION public.disease_cases_default_disease_id_iso3_iso_year_iso_week_sou_idx;


--
-- Name: disease_cases_default_iso3_disease_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_disease_cases_lookup ATTACH PARTITION public.disease_cases_default_iso3_disease_id_iso_year_iso_week_idx;


--
-- Name: disease_cases_default_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.disease_cases_pkey ATTACH PARTITION public.disease_cases_default_pkey;


--
-- Name: predictions_2022_disease_id_iso3_iso_year_iso_week_horizon__idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_predictions_unique ATTACH PARTITION public.predictions_2022_disease_id_iso3_iso_year_iso_week_horizon__idx;


--
-- Name: predictions_2022_disease_id_iso_year_iso_week_risk_level_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_predictions_dashboard ATTACH PARTITION public.predictions_2022_disease_id_iso_year_iso_week_risk_level_idx;


--
-- Name: predictions_2022_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.predictions_pkey ATTACH PARTITION public.predictions_2022_pkey;


--
-- Name: predictions_2023_disease_id_iso3_iso_year_iso_week_horizon__idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_predictions_unique ATTACH PARTITION public.predictions_2023_disease_id_iso3_iso_year_iso_week_horizon__idx;


--
-- Name: predictions_2023_disease_id_iso_year_iso_week_risk_level_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_predictions_dashboard ATTACH PARTITION public.predictions_2023_disease_id_iso_year_iso_week_risk_level_idx;


--
-- Name: predictions_2023_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.predictions_pkey ATTACH PARTITION public.predictions_2023_pkey;


--
-- Name: predictions_default_disease_id_iso3_iso_year_iso_week_horiz_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_predictions_unique ATTACH PARTITION public.predictions_default_disease_id_iso3_iso_year_iso_week_horiz_idx;


--
-- Name: predictions_default_disease_id_iso_year_iso_week_risk_level_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_predictions_dashboard ATTACH PARTITION public.predictions_default_disease_id_iso_year_iso_week_risk_level_idx;


--
-- Name: predictions_default_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.predictions_pkey ATTACH PARTITION public.predictions_default_pkey;


--
-- Name: weather_obs_2010_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2010_data_idx;


--
-- Name: weather_obs_2010_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2010_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2010_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2010_pkey;


--
-- Name: weather_obs_2011_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2011_data_idx;


--
-- Name: weather_obs_2011_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2011_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2011_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2011_pkey;


--
-- Name: weather_obs_2012_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2012_data_idx;


--
-- Name: weather_obs_2012_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2012_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2012_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2012_pkey;


--
-- Name: weather_obs_2013_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2013_data_idx;


--
-- Name: weather_obs_2013_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2013_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2013_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2013_pkey;


--
-- Name: weather_obs_2014_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2014_data_idx;


--
-- Name: weather_obs_2014_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2014_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2014_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2014_pkey;


--
-- Name: weather_obs_2015_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2015_data_idx;


--
-- Name: weather_obs_2015_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2015_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2015_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2015_pkey;


--
-- Name: weather_obs_2016_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2016_data_idx;


--
-- Name: weather_obs_2016_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2016_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2016_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2016_pkey;


--
-- Name: weather_obs_2017_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2017_data_idx;


--
-- Name: weather_obs_2017_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2017_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2017_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2017_pkey;


--
-- Name: weather_obs_2018_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2018_data_idx;


--
-- Name: weather_obs_2018_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2018_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2018_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2018_pkey;


--
-- Name: weather_obs_2019_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2019_data_idx;


--
-- Name: weather_obs_2019_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2019_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2019_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2019_pkey;


--
-- Name: weather_obs_2022_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_2022_data_idx;


--
-- Name: weather_obs_2022_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_2022_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_2022_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_2022_pkey;


--
-- Name: weather_obs_default_data_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_data_gin ATTACH PARTITION public.weather_obs_default_data_idx;


--
-- Name: weather_obs_default_iso3_source_id_iso_year_iso_week_idx; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.idx_weather_unique ATTACH PARTITION public.weather_obs_default_iso3_source_id_iso_year_iso_week_idx;


--
-- Name: weather_obs_default_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.weather_observations_pkey ATTACH PARTITION public.weather_obs_default_pkey;


--
-- Name: data_quality_checks data_quality_checks_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_checks
    ADD CONSTRAINT data_quality_checks_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.pipeline_runs(run_id);


--
-- Name: disease_cases disease_cases_disease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.disease_cases
    ADD CONSTRAINT disease_cases_disease_id_fkey FOREIGN KEY (disease_id) REFERENCES public.diseases(id);


--
-- Name: disease_cases disease_cases_iso3_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.disease_cases
    ADD CONSTRAINT disease_cases_iso3_fkey FOREIGN KEY (iso3) REFERENCES public.countries(iso3);


--
-- Name: disease_cases disease_cases_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.disease_cases
    ADD CONSTRAINT disease_cases_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.data_sources(id);


--
-- Name: feature_configs feature_configs_disease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_configs
    ADD CONSTRAINT feature_configs_disease_id_fkey FOREIGN KEY (disease_id) REFERENCES public.diseases(id);


--
-- Name: feature_snapshots feature_snapshots_disease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_snapshots
    ADD CONSTRAINT feature_snapshots_disease_id_fkey FOREIGN KEY (disease_id) REFERENCES public.diseases(id);


--
-- Name: feature_snapshots feature_snapshots_iso3_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_snapshots
    ADD CONSTRAINT feature_snapshots_iso3_fkey FOREIGN KEY (iso3) REFERENCES public.countries(iso3);


--
-- Name: model_evaluations model_evaluations_model_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_evaluations
    ADD CONSTRAINT model_evaluations_model_version_id_fkey FOREIGN KEY (model_version_id) REFERENCES public.model_versions(id);


--
-- Name: model_versions model_versions_disease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_versions
    ADD CONSTRAINT model_versions_disease_id_fkey FOREIGN KEY (disease_id) REFERENCES public.diseases(id);


--
-- Name: predictions predictions_disease_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.predictions
    ADD CONSTRAINT predictions_disease_id_fkey FOREIGN KEY (disease_id) REFERENCES public.diseases(id);


--
-- Name: predictions predictions_iso3_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.predictions
    ADD CONSTRAINT predictions_iso3_fkey FOREIGN KEY (iso3) REFERENCES public.countries(iso3);


--
-- Name: predictions predictions_model_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.predictions
    ADD CONSTRAINT predictions_model_version_id_fkey FOREIGN KEY (model_version_id) REFERENCES public.model_versions(id);


--
-- Name: weather_observations weather_observations_iso3_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.weather_observations
    ADD CONSTRAINT weather_observations_iso3_fkey FOREIGN KEY (iso3) REFERENCES public.countries(iso3);


--
-- Name: weather_observations weather_observations_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.weather_observations
    ADD CONSTRAINT weather_observations_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.data_sources(id);


--
-- Name: weather_variables weather_variables_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weather_variables
    ADD CONSTRAINT weather_variables_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.data_sources(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Cbmx4yIaPvyQsd3caJ2h7yUDyCsPzRystXesbPsIopEpRmgmR9IyelaC4H2ROxf

