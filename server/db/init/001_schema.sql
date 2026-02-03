create table if not exists sales_daily (
  date date not null,
  store_id text not null,
  sku text not null,
  qty numeric(18,3) not null default 0,
  primary key (date, store_id, sku)
);

create table if not exists stock_daily (
  date date not null,
  store_id text not null,
  sku text not null,
  on_hand numeric(18,3) not null default 0,
  primary key (date, store_id, sku)
);

create table if not exists sku_params (
  sku text primary key,
  min_pack numeric(18,3) not null default 0,
  pack_multiple numeric(18,3) not null default 1,
  lead_time_days int not null default 3
);

create table if not exists forecast_daily (
  date date not null,
  store_id text not null,
  sku text not null,
  forecast_qty numeric(18,3) not null default 0,
  primary key (date, store_id, sku)
);

create table if not exists replenishment (
  calc_date date not null,
  store_id text not null,
  sku text not null,
  forecast_sum numeric(18,3) not null default 0,
  safety_stock numeric(18,3) not null default 0,
  recommended_order numeric(18,3) not null default 0,
  reason_json jsonb not null default '[]'::jsonb,
  primary key (calc_date, store_id, sku)
);

create index if not exists idx_sales_store_sku_date on sales_daily(store_id, sku, date);
create index if not exists idx_stock_store_sku_date on stock_daily(store_id, sku, date);
create index if not exists idx_repl_store_date on replenishment(store_id, calc_date);

