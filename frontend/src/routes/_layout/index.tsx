import { createFileRoute } from "@tanstack/react-router";
import { Hero } from '@/components/Hero';
import { FeaturedProducts } from '@/components/FeaturedProducts';
import { useFeaturedProducts } from '@/hooks/useProducts';

export const Route = createFileRoute("/_layout/")({
  component: HomePage,
});

export function HomePage() {
  const { data: products = [], isLoading, error } = useFeaturedProducts(8);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">⚠️</span>
          </div>
          <h2 className="text-2xl font-semibold text-[#0F172A] mb-2">
            Something went wrong
          </h2>
          <p className="text-[#6B7280]">
            Unable to load products. Please try again later.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Hero />
      <FeaturedProducts 
        products={products} 
        isLoading={isLoading}
        title="New Arrivals"
        subtitle="Be the first to discover our latest fashion pieces"
      />
      
      {/* Additional sections can be added here */}
      <section className="py-16 bg-[#F7F7F8]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-[#0F172A] mb-6">
            Why Choose Fashion?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
            <div className="text-center">
              <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">✨</span>
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">
                Quality Materials
              </h3>
              <p className="text-[#6B7280]">
                We source only the finest fabrics and materials for lasting comfort and style.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">
                Perfect Fit
              </h3>
              <p className="text-[#6B7280]">
                Every piece is designed with attention to detail for the perfect fit.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🚀</span>
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">
                Fast Delivery
              </h3>
              <p className="text-[#6B7280]">
                Quick and reliable shipping to get your new style to you fast.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
