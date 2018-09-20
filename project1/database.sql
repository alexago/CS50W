-- Adminer 4.6.3-dev PostgreSQL dump

CREATE SEQUENCE books_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

CREATE TABLE "public"."books" (
    "id" integer DEFAULT nextval('books_id_seq') NOT NULL,
    "title" character varying NOT NULL,
    "author" character varying NOT NULL,
    "year" integer NOT NULL,
    "isbn" character varying NOT NULL,
    CONSTRAINT "books_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


CREATE SEQUENCE reviews_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

CREATE TABLE "public"."reviews" (
    "id" integer DEFAULT nextval('reviews_id_seq') NOT NULL,
    "user_id" integer NOT NULL,
    "book_id" integer NOT NULL,
    "review" text NOT NULL,
    "rating" smallint NOT NULL
) WITH (oids = false);


CREATE SEQUENCE users_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

CREATE TABLE "public"."users" (
    "id" integer DEFAULT nextval('users_id_seq') NOT NULL,
    "username" text NOT NULL,
    "password" text NOT NULL
) WITH (oids = false);


-- 2018-09-20 12:36:03.423104+00
