import { Button } from '@/components/ui/button';
import { FASHION_THEME } from '@/lib/constants';

export function Hero() {
  return (
    <section className="relative bg-gradient-to-r from-[#F7F7F8] to-[#E5E7EB] overflow-hidden">
      <div className={FASHION_THEME.spacing.container}>
        <div className="relative z-10 py-20 lg:py-32">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Content */}
            <div className="text-center lg:text-left">
              <h1 className="text-4xl lg:text-6xl font-bold text-[#0F172A] mb-6 leading-tight">
                Discover Your
                <span className="block text-[#C99B6A]">Perfect Style</span>
              </h1>
              <p className="text-lg text-[#6B7280] mb-8 max-w-lg mx-auto lg:mx-0">
                Explore our curated collection of timeless fashion pieces. From casual essentials 
                to statement pieces, find what makes you feel confident and beautiful.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Button 
                  size="lg" 
                  className="bg-[#C99B6A] hover:bg-[#B08A5A] text-white px-8 py-3 text-lg"
                >
                  Shop Now
                </Button>
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="border-[#C99B6A] text-[#C99B6A] hover:bg-[#C99B6A] hover:text-white px-8 py-3 text-lg"
                >
                  View Collections
                </Button>
              </div>
            </div>

            {/* Visual Element */}
            <div className="relative">
              <div className="relative z-10">
                <div className="w-full h-96 lg:h-[500px] bg-gradient-to-br from-[#C99B6A] to-[#1F6F8B] rounded-2xl shadow-2xl flex items-center justify-center">
                  <div className="text-center text-white">
                    <div className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center mb-4 mx-auto">
                      <span className="text-4xl">👗</span>
                    </div>
                    <p className="text-xl font-medium">Fashion Forward</p>
                    <p className="text-sm opacity-90">Discover the latest trends</p>
                  </div>
                </div>
              </div>
              
              {/* Decorative elements */}
              <div className="absolute -top-4 -right-4 w-20 h-20 bg-[#C99B6A] rounded-full opacity-20"></div>
              <div className="absolute -bottom-4 -left-4 w-16 h-16 bg-[#1F6F8B] rounded-full opacity-20"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000' fill-opacity='1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}></div>
      </div>
    </section>
  );
} 