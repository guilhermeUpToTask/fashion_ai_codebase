import { Button } from '@/components/ui/button';
import { FASHION_THEME } from '@/lib/constants';
import { Upload, Search, Brain } from 'lucide-react';

export function Hero() {
  return (
    <section className="relative bg-gradient-to-br from-[#F7F7F8] via-white to-[#E5E7EB] overflow-hidden">
      <div className={FASHION_THEME.spacing.container}>
        <div className="relative z-10 py-20 lg:py-32">
          <div className="text-center max-w-4xl mx-auto">
            {/* Main Headline */}
            <div className="mb-8">
              <h1 className="text-4xl lg:text-6xl font-bold text-[#0F172A] mb-6 leading-tight">
                Fashion AI
                <span className="block text-[#C99B6A]">Image Search</span>
              </h1>
              <p className="text-xl lg:text-2xl text-[#6B7280] max-w-3xl mx-auto leading-relaxed">
                A proof of concept demonstrating AI-powered visual search for fashion using 
                <span className="font-semibold text-[#1F6F8B]"> YOLOv8</span> and 
                <span className="font-semibold text-[#1F6F8B]"> CLIP</span> models
              </p>
            </div>

            {/* Two Main Features */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
              {/* Feature 1: Index Products */}
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 shadow-lg">
                <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-4">
                  <Upload className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-[#0F172A] mb-3">
                  Index Product Images
                </h3>
                <p className="text-[#6B7280] mb-4">
                  Upload product images to be automatically processed by AI. 
                  The system detects clothing items, generates semantic labels, 
                  and stores them in a vector database for similarity search.
                </p>
                <Button 
                  size="lg" 
                  className="bg-[#C99B6A] hover:bg-[#B08A5A] text-white px-6 py-3"
                >
                  <Upload className="w-5 h-5 mr-2" />
                  Index Products
                </Button>
              </div>

              {/* Feature 2: Query Similar */}
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 shadow-lg">
                <div className="w-16 h-16 bg-[#1F6F8B] rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-[#0F172A] mb-3">
                  Find Similar Clothes
                </h3>
                <p className="text-[#6B7280] mb-4">
                  Upload any image containing clothing to find visually similar 
                  products from your indexed catalog using AI-powered similarity search.
                </p>
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="border-[#1F6F8B] text-[#1F6F8B] hover:bg-[#1F6F8B] hover:text-white px-6 py-3"
                >
                  <Search className="w-5 h-5 mr-2" />
                  Search Similar
                </Button>
              </div>
            </div>

            {/* Tech Stack */}
            <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 border border-gray-200">
              <h4 className="text-lg font-semibold text-[#0F172A] mb-4 flex items-center justify-center">
                <Brain className="w-5 h-5 mr-2 text-[#C99B6A]" />
                Powered by Advanced AI Models
              </h4>
              <div className="flex flex-wrap justify-center gap-4 text-sm">
                <span className="bg-[#C99B6A]/10 text-[#C99B6A] px-3 py-1 rounded-full font-medium">
                  YOLOv8 - Object Detection
                </span>
                <span className="bg-[#1F6F8B]/10 text-[#1F6F8B] px-3 py-1 rounded-full font-medium">
                  CLIP - Semantic Understanding
                </span>
                <span className="bg-[#6B7280]/10 text-[#6B7280] px-3 py-1 rounded-full font-medium">
                  Vector Database
                </span>
                <span className="bg-[#C99B6A]/10 text-[#C99B6A] px-3 py-1 rounded-full font-medium">
                  Async Processing
                </span>
              </div>
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