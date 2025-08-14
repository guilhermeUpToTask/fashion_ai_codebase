# Fashion Storefront UI Components

This document describes the UI components and layout structure for the fashion storefront.

## 🎨 Design System

### Color Palette
- **Neutral Background**: `#F7F7F8` (light gray)
- **Primary Text**: `#0F172A` (dark blue)
- **Muted Text**: `#6B7280` (medium gray)
- **Accent**: `#C99B6A` (warm gold/mustard)
- **Secondary**: `#1F6F8B` (teal)

### Typography
- **Headings**: Large, bold text for product titles and section headers
- **Body**: 14-16px base text for descriptions and content
- **System Font Stack**: Uses system default fonts for optimal performance

## 🧩 Core Components

### Layout Components
- **Header** (`src/components/Header.tsx`): Navigation bar with logo, search, and user actions
- **Footer** (`src/components/Footer.tsx`): Footer with links, social media, and company info
- **Layout** (`src/routes/_layout.tsx`): Main layout wrapper that includes header and footer

### Page Components
- **Hero** (`src/components/Hero.tsx`): Landing page hero section with call-to-action
- **FeaturedProducts** (`src/components/FeaturedProducts.tsx`): Product grid with loading states
- **ProductCard** (`src/components/ProductCard.tsx`): Individual product display card

### UI Components
- **Skeleton** (`src/components/ui/skeleton.tsx`): Loading state placeholders
- **ProductSkeleton** (`src/components/ProductSkeleton.tsx`): Product-specific loading states

## 🔧 Data Fetching

### Hooks
- **useProducts** (`src/hooks/useProducts.ts`): Fetch product lists and individual products
- **useFeaturedProducts**: Get featured products for the homepage

### API Integration
- Uses the generated SDK client (`src/client/sdk.gen.ts`)
- TanStack Query for data fetching and caching
- TypeScript types from generated types (`src/client/types.gen.ts`)

## 📱 Responsive Design

- **Mobile First**: Components designed for mobile and scale up to desktop
- **Breakpoints**: Uses Tailwind's responsive utilities (sm, md, lg, xl)
- **Grid System**: Responsive grid layouts that adapt to screen size

## 🚀 Getting Started

### Development
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run linter (note: SDK files may have warnings)
```

### Component Usage
```tsx
import { Header } from '@/components/Header';
import { FeaturedProducts } from '@/components/FeaturedProducts';

// Use in your component
<Header />
<FeaturedProducts products={products} isLoading={isLoading} />
```

## 🔮 Future Enhancements

- **Cart Functionality**: Full shopping cart implementation
- **Product Filters**: Category, price, and search filtering
- **Product Detail Pages**: Individual product views
- **User Authentication**: Login/signup flows
- **Checkout Process**: Complete purchase flow

## 📁 File Structure

```
src/
├── components/           # Main UI components
│   ├── ui/             # Reusable UI components (shadcn)
│   ├── Header.tsx      # Navigation header
│   ├── Footer.tsx      # Site footer
│   ├── Hero.tsx        # Landing hero section
│   ├── ProductCard.tsx # Product display card
│   └── ...
├── hooks/               # Data fetching hooks
├── lib/                 # Utilities and constants
└── routes/              # Page components and routing
```

## 🎯 Key Features

- **Modern Design**: Clean, fashion-forward aesthetic
- **Performance**: Optimized with TanStack Query and React best practices
- **Accessibility**: Semantic HTML and ARIA attributes
- **Type Safety**: Full TypeScript integration with generated types
- **Responsive**: Works seamlessly across all device sizes 