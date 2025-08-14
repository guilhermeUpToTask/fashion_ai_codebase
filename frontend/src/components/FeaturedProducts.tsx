import { ProductCard } from './ProductCard';
import { ProductGridSkeleton } from './ProductSkeleton';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import { FASHION_THEME } from '@/lib/constants';
import type { Product } from '@/client/types.gen';

interface FeaturedProductsProps {
  products: Product[];
  title?: string;
  subtitle?: string;
  showViewAll?: boolean;
  isLoading?: boolean;
}

export function FeaturedProducts({ 
  products, 
  title = "Featured Products", 
  subtitle = "Discover our most popular items",
  showViewAll = true,
  isLoading = false
}: FeaturedProductsProps) {
  const handleAddToCart = (product: Product) => {
    // TODO: Implement add to cart functionality
    console.log('Add to cart:', product);
  };

  return (
    <section className="py-16 bg-white">
      <div className={FASHION_THEME.spacing.container}>
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-[#0F172A] mb-4">
            {title}
          </h2>
          <p className="text-lg text-[#6B7280] max-w-2xl mx-auto">
            {subtitle}
          </p>
        </div>

        {/* Products Grid */}
        {isLoading ? (
          <ProductGridSkeleton count={8} />
        ) : products.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-12">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">👕</span>
            </div>
            <h3 className="text-xl font-semibold text-[#0F172A] mb-2">
              No products available
            </h3>
            <p className="text-[#6B7280]">
              Check back soon for new arrivals!
            </p>
          </div>
        )}

        {/* View All Button */}
        {showViewAll && products.length > 0 && !isLoading && (
          <div className="text-center">
            <Button 
              variant="outline" 
              size="lg"
              className="border-[#C99B6A] text-[#C99B6A] hover:bg-[#C99B6A] hover:text-white px-8 py-3"
            >
              View All Products
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        )}
      </div>
    </section>
  );
} 