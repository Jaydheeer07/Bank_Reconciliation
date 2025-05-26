--
-- PostgreSQL database dump
--

-- Dumped from database version 15.10 (Debian 15.10-1.pgdg120+1)
-- Dumped by pg_dump version 15.10 (Debian 15.10-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: bank_reconciliation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bank_reconciliation (
    id integer NOT NULL,
    client_name character varying NOT NULL,
    account_name character varying NOT NULL,
    transaction_date date NOT NULL,
    payee character varying NOT NULL,
    particulars character varying NOT NULL,
    spent numeric(10,2),
    received numeric(10,2),
    file_name character varying NOT NULL,
    insert_time date NOT NULL,
    inserted_by character varying NOT NULL,
    start_date date,
    end_date date,
    min_amount numeric(10,2),
    max_amount numeric(10,2),
    details character varying,
    name_ref character varying,
    exact_amount numeric(10,2)
);


ALTER TABLE public.bank_reconciliation OWNER TO postgres;

--
-- Name: bank_reconciliation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bank_reconciliation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bank_reconciliation_id_seq OWNER TO postgres;

--
-- Name: bank_reconciliation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bank_reconciliation_id_seq OWNED BY public.bank_reconciliation.id;


--
-- Name: blacklisted_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.blacklisted_tokens (
    id uuid NOT NULL,
    token character varying NOT NULL,
    blacklisted_at timestamp without time zone,
    expires_at timestamp without time zone NOT NULL
);


ALTER TABLE public.blacklisted_tokens OWNER TO postgres;

--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.password_reset_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    token character varying NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.password_reset_tokens OWNER TO postgres;

--
-- Name: refresh_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.refresh_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    token character varying NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone,
    is_revoked boolean
);


ALTER TABLE public.refresh_tokens OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_active boolean,
    is_verified boolean,
    last_login timestamp without time zone,
    is_superuser boolean,
    role character varying,
    failed_login_attempts integer,
    last_failed_login timestamp without time zone,
    locked_until timestamp without time zone,
    last_successful_login timestamp without time zone,
    brain_name character varying,
    brain_id character varying
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: bank_reconciliation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank_reconciliation ALTER COLUMN id SET DEFAULT nextval('public.bank_reconciliation_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
4a9b2025fbc9
\.


--
-- Data for Name: bank_reconciliation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bank_reconciliation (id, client_name, account_name, transaction_date, payee, particulars, spent, received, file_name, insert_time, inserted_by, start_date, end_date, min_amount, max_amount, details, name_ref, exact_amount) FROM stdin;
\.


--
-- Data for Name: blacklisted_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.blacklisted_tokens (id, token, blacklisted_at, expires_at) FROM stdin;
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.password_reset_tokens (id, user_id, token, expires_at, created_at) FROM stdin;
\.


--
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.refresh_tokens (id, user_id, token, expires_at, created_at, is_revoked) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, hashed_password, created_at, updated_at, is_active, is_verified, last_login, is_superuser, role, failed_login_attempts, last_failed_login, locked_until, last_successful_login, brain_name, brain_id) FROM stdin;
ebaa40d7-8870-4c20-b80a-78579ef8581e	migsss@example.com	$2b$12$V9.6IGdSgrBLkablNe.RLuk/eMR/GKLn0Ypgz4ggDvmENxnCgghC6	2025-01-08 05:48:36.305372	2025-01-08 05:48:36.30546	t	f	\N	f	user	0	\N	\N	\N	\N	\N
aefb8e6a-8d7c-463c-98cf-e9c3256b52cd	jordanss@example.com	$2b$12$UXtEeGBNW9KUWDo0MACbE.3LNgX5cLPdmM1kKgfOmOGSxgdvjfhUG	2025-01-08 05:48:36.305372	2025-01-08 05:48:36.30546	t	f	\N	f	user	0	\N	\N	\N	\N	\N
6ce35090-9e51-4d39-9145-8728bc35d3dc	dherickszz@example.com	$2b$12$.zNaLx5GzYzwyNDXP.UANeoqArG8o8zvQoiKZ80zSMuM.B7EV9oBq	2025-01-09 02:31:13.067525	2025-01-09 02:31:13.067608	t	f	\N	f	user	0	\N	\N	\N	\N	\N
4ad056cc-c09a-4aca-aaf6-a3ea285c4aec	narutozzzz@example.com	$2b$12$VyD1AkjjYE/FX4DhvvLv6OjDx9AQhd3ZoZFN0J.7JNUTGgZvZVsje	2025-01-09 02:39:39.559979	2025-01-09 02:39:39.560103	t	f	\N	f	user	0	\N	\N	\N	\N	\N
c0ec3a73-9f0a-4f7f-a588-7c5345d34ec3	sasukezzz@example.com	$2b$12$BHhEpUXKNWrh0HJSvTGY/O4ypRMlT8RB.3AY4/fdFT3PU.qBfUcJe	2025-01-09 02:52:41.090554	2025-01-09 02:52:41.09064	t	f	\N	f	user	0	\N	\N	\N	\N	\N
13aa9f0f-8041-4cf3-ab35-9a7e107dc124	uchiha_obito@example.com	$2b$12$tGMeuMtEPjMIJh/ucu0WI.JBKfVH9S9SDz8jJYfoEtZrytL6YDrcm	2025-01-09 02:59:00.234968	2025-01-09 02:59:00.235045	t	f	\N	f	user	0	\N	\N	\N	\N	\N
d12e9be2-2741-499b-ad3a-a01af2134052	dhejiou@example.com	$2b$12$J.VOd6PJ/1l/ZExoH/G/6ePYYF4ZFjmhcR8WcAaP5p4WTlg7az5We	2025-01-09 04:21:59.244734	2025-01-09 04:21:59.244811	t	f	\N	f	user	0	\N	\N	\N	brain_dhejiou@example.com	brain_9a34aabf-1553-40a2-98bc-7413e3cb22a0
a7b61dd4-f385-4ebf-85b7-151ea29d435b	edzzz@example.com	$2b$12$fkud4QlGK3mbWmzt7YBu/ORLkuw1aJwKTPt/PwtTYif4wt6o2awHW	2025-01-09 06:07:46.275192	2025-01-09 06:07:46.275275	t	f	\N	f	user	0	\N	\N	\N	brain_edzzz@example.com	brain_0b837298-bb1b-408f-b3fb-e7ed92aa82d8
\.


--
-- Name: bank_reconciliation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bank_reconciliation_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: bank_reconciliation bank_reconciliation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bank_reconciliation
    ADD CONSTRAINT bank_reconciliation_pkey PRIMARY KEY (id);


--
-- Name: blacklisted_tokens blacklisted_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_pkey PRIMARY KEY (id);


--
-- Name: blacklisted_tokens blacklisted_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_token_key UNIQUE (token);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_key UNIQUE (token);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_key UNIQUE (token);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_blacklisted_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_blacklisted_tokens_token ON public.blacklisted_tokens USING btree (token);


--
-- Name: ix_refresh_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_refresh_tokens_token ON public.refresh_tokens USING btree (token);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: refresh_tokens refresh_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

