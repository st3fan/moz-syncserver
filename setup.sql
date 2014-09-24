-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at http://mozilla.org/MPL/2.0/

-- From moz-tokenserver/setup.sql
create table Users (
  Uid          serial not null unique primary key,
  Created      timestamp without time zone default (now() at time zone 'utc'),
  Email        varchar unique not null,
  Generation   bigint not null,
  ClientState  varchar not null
)

-- From moz-syncserver/setup.sql
create table Objects (
  UserId             integer not null,
  CollectionName     varchar(32) not null,
  Id                 varchar(64) not null,
  primary key (UserId, CollectionName, Id),
  SortIndex          integer,
  Modified           bigint not null,
  Payload            text not null default '',
  PayloadSize        integer not null default 0,
  TTL                integer not null default 2100000000
);
