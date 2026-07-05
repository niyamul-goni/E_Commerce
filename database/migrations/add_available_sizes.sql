-- ============================================================
-- Migration: Add available_sizes column to products table
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

ALTER TABLE products
  ADD COLUMN IF NOT EXISTS available_sizes VARCHAR(500);

-- Example: update products with size data
-- UPDATE products SET available_sizes = 'XS,S,M,L,XL,XXL' WHERE id = 1;
