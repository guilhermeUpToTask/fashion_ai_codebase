import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function ProductSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="relative">
        {/* Image skeleton */}
        <Skeleton className="aspect-square w-full" />
      </div>
      <CardContent className="p-4">
        <div className="space-y-2">
          {/* Title skeleton */}
          <Skeleton className="h-6 w-3/4" />
          
          {/* Description skeleton */}
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          
          {/* SKU skeleton */}
          <Skeleton className="h-3 w-1/2" />
          
          {/* Price skeleton */}
          <div className="pt-2">
            <Skeleton className="h-6 w-20" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: count }).map((_, index) => (
        <ProductSkeleton key={index} />
      ))}
    </div>
  );
} 