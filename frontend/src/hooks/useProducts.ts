import { useQuery } from '@tanstack/react-query';
import { Products } from '@/client/sdk.gen';

export function useProducts(limit?: number) {
  return useQuery({
    queryKey: ['products', { limit }],
    queryFn: async () => {
      const response = await Products.listProducts({
        query: { limit: limit || 20 }
      });
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useProduct(productId: string) {
  return useQuery({
    queryKey: ['product', productId],
    queryFn: async () => {
      const response = await Products.getProduct({
        path: { product_id: productId }
      });
      return response.data;
    },
    enabled: !!productId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useFeaturedProducts(limit: number = 8) {
  return useQuery({
    queryKey: ['featured-products', { limit }],
    queryFn: async () => {
      const response = await Products.listProducts({
        query: { limit }
      });
      return response.data;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
} 