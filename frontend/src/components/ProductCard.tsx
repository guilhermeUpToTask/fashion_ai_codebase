import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Heart, ShoppingBag, Image as ImageIcon } from 'lucide-react';
import type { Product } from '@/client/types.gen';

interface ProductWithImages extends Product {
  image_ids: string[];
}

interface ProductCardProps {
  product: ProductWithImages;
  onAddToCart?: (product: ProductWithImages) => void;
}

export function ProductCard({ product, onAddToCart }: ProductCardProps) {
  const handleAddToCart = () => {
    if (onAddToCart) {
      onAddToCart(product);
    }
  };

  // Get the first image ID for display (you can implement image carousel later)
  const primaryImageId = product.image_ids?.[0];
  return (
    <Card className="group overflow-hidden hover:shadow-lg transition-all duration-300 border-gray-200 hover:border-[#C99B6A]">
      <div className="relative">
        {/* Product Image */}
        {primaryImageId ? (
          <div className="aspect-square bg-gray-100 overflow-hidden">
            <img
            //TODO: needs to fix the source link for the image, should point to the backend endpoint where its download the image
              src={`${import.meta.env.VITE_API_URL}/api/images/${primaryImageId}/download`}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              onError={(e) => {
                // Fallback to placeholder if image fails to load
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                target.nextElementSibling?.classList.remove('hidden');
              }}
            />
            {/* Fallback placeholder (hidden by default) */}
            <div className="aspect-square bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center hidden">
              <div className="text-center">
                <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-2">
                  <ImageIcon className="w-8 h-8 text-white" />
                </div>
                <p className="text-sm text-gray-500">Image Unavailable</p>
              </div>
            </div>
          </div>
        ) : (
          // No image available - show placeholder
          <div className="aspect-square bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-2">
                <ImageIcon className="w-8 h-8 text-white" />
              </div>
              <p className="text-sm text-gray-500">No Image</p>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="icon"
            className="w-8 h-8 bg-white/90 hover:bg-white shadow-sm"
          >
            <Heart className="w-4 h-4 text-gray-600" />
          </Button>
        </div>

        {/* Add to Cart Button */}
        <div className="absolute bottom-3 left-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            onClick={handleAddToCart}
            className="w-full bg-[#C99B6A] hover:bg-[#B08A5A] text-white"
            size="sm"
          >
            <ShoppingBag className="w-4 h-4 mr-2" />
            Add to Cart
          </Button>
        </div>
      </div>

      <CardContent className="p-4">
        {/* Product Info */}
        <div className="space-y-2">
          <h3 className="font-semibold text-[#0F172A] text-lg line-clamp-2 group-hover:text-[#C99B6A] transition-colors">
            {product.name}
          </h3>
          
          {product.description && (
            <p className="text-[#6B7280] text-sm line-clamp-2">
              {product.description}
            </p>
          )}

          {product.sku && (
            <p className="text-xs text-[#6B7280] font-mono">
              SKU: {product.sku}
            </p>
          )}

          {/* Price */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-xl font-bold text-[#0F172A]">
              ${parseFloat(product.price).toFixed(2)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 