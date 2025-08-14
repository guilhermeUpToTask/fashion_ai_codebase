export const FASHION_THEME = {
  colors: {
    neutral: '#F7F7F8',
    text: '#0F172A',
    muted: '#6B7280',
    accent: '#C99B6A',
    secondary: '#1F6F8B',
  },
  spacing: {
    container: 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
  },
} as const;

export const PRODUCT_CATEGORIES = [
  'All',
  'Clothing',
  'Shoes',
  'Accessories',
  'Jewelry',
  'Bags',
] as const;

export const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest First' },
  { value: 'price-low', label: 'Price: Low to High' },
  { value: 'price-high', label: 'Price: High to Low' },
  { value: 'name-asc', label: 'Name: A to Z' },
  { value: 'name-desc', label: 'Name: Z to A' },
] as const;

export const PRICE_RANGES = [
  { min: 0, max: 50, label: 'Under $50' },
  { min: 50, max: 100, label: '$50 - $100' },
  { min: 100, max: 200, label: '$100 - $200' },
  { min: 200, max: 500, label: '$200 - $500' },
  { min: 500, max: null, label: 'Over $500' },
] as const; 