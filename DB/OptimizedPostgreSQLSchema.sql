-- Drop existing schema and recreate (only run if needed)
-- DROP SCHEMA public CASCADE;
CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION pg_database_owner;

-- Users Table
CREATE TABLE public.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    chat_id BIGINT NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_chat_id ON public.users(chat_id);

-- Routes Table (No ENUM, No Status)
CREATE TABLE public.routes_req (
    route_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    start_location VARCHAR(255) NOT NULL,
    end_location VARCHAR(255) NOT NULL,
    route_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE
);
CREATE INDEX idx_routes_user_id ON public.routes_req(user_id);

-- Attractions Table
CREATE TABLE public.attractions_res (
    attraction_id SERIAL PRIMARY KEY,
    route_id INT NOT NULL,
    attraction_name VARCHAR(255) NOT NULL, -- Renamed from "name" to avoid reserved keyword issues
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    address TEXT,
    category VARCHAR(100),
    audience_type VARCHAR(50),
    popularity NUMERIC(3,1), -- Optimized from VARCHAR to NUMERIC
    opening_hours JSONB CHECK (jsonb_typeof(opening_hours) = 'array'), -- Ensures JSON array format
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (route_id) REFERENCES public.routes_req(route_id) ON DELETE CASCADE
);
CREATE INDEX idx_attractions_route_id ON public.attractions_res(route_id);

-- Breaks Table
CREATE TABLE public.breaks_res (
    break_id SERIAL PRIMARY KEY,
    route_id INT NOT NULL,
    break_type VARCHAR(50) NOT NULL, -- Kept VARCHAR instead of ENUM
    break_name VARCHAR(255),
    break_address VARCHAR(255),
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    working_hours JSONB CHECK (jsonb_typeof(working_hours) = 'array'), -- Ensures JSON array format
    rating NUMERIC(3,1) CHECK (rating BETWEEN 0 AND 5), -- Ensures valid rating between 0 and 5
    url VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (route_id) REFERENCES public.routes_req(route_id) ON DELETE CASCADE
);
CREATE INDEX idx_breaks_route_id ON public.breaks_res(route_id);


-- gas-stations Table
CREATE TABLE public.gas_stations_res (
    place_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255),
    address VARCHAR(255),
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    working_hours VARCHAR(255),
    rating NUMERIC(3,1) CHECK (rating BETWEEN 0 AND 5), -- Ensures valid rating between 0 and 5
    url VARCHAR(255),
    vicinity VARCHAR(255),
    wheelchair_accessible BOOLEAN,
    petrol98 BOOLEAN,
    electric_charge BOOLEAN,
    convenient_store BOOLEAN,
    car_wash BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_gas_station_id ON public.gas_stations_res(place_id);


-- gas-stations Table
CREATE TABLE public.restaurants_res (
    place_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255),
    address VARCHAR(255),
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    working_hours VARCHAR(255),
    rating NUMERIC(3,1) CHECK (rating BETWEEN 0 AND 5), -- Ensures valid rating between 0 and 5
    url VARCHAR(255),
    vicinity VARCHAR(255),
    wheelchair_accessible BOOLEAN,
    serves_alcohol BOOLEAN,
    price_level NUMERIC(3,1) CHECK (price_level BETWEEN 1 AND 4), -- Ensures valid rating between 1 and 4,
    website VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_restaurant_id ON public.restaurants_res(place_id);


