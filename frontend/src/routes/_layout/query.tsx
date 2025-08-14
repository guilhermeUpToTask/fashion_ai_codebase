import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FASHION_THEME } from "@/lib/constants";
import { Search, Image as ImageIcon, Clock, CheckCircle, XCircle } from "lucide-react";
import { useQueryingJob, useJobStatus } from "@/hooks/useJobs";
import { toast } from "sonner";

export const Route = createFileRoute("/_layout/query")({
  component: QueryPage,
});

interface ClothMatch {
  image_id: string;
  score: number;
  rank: number;
  product_id?: string;
  product_name?: string;
  product_description?: string;
}

interface ClothResult {
  cloth_id: string;
  crop_img_id: string;
  matched_images: ClothMatch[];
}

interface QueryResult {
  type: 'querying';
  model_version: string;
  cloths: ClothResult[];
}

export function QueryPage() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const queryingJobMutation = useQueryingJob();
  const { data: jobStatus } = useJobStatus(currentJobId || "");

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      // Create preview URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleQueryImage = async () => {
    if (!selectedImage) {
      toast.error("Please select an image first");
      return;
    }

    try {
      const result = await queryingJobMutation.mutateAsync({ imageFile: selectedImage });
      if (result?.job_id) {
        setCurrentJobId(result.job_id);
        toast.success("Image query job started! Processing your image...");
      }
    } catch {
      toast.error("Failed to start query job");
    }
  };

  const getJobStatusIcon = () => {
    if (!jobStatus) return null;
    
    switch (jobStatus.status) {
      case 'queued':
      case 'started':
      case 'detecting':
      case 'labelling':
      case 'querying':
        return <Clock className="w-5 h-5 text-[#C99B6A] animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return null;
    }
  };

  const getJobStatusText = () => {
    if (!jobStatus) return "";
    
    switch (jobStatus.status) {
      case 'queued':
        return "Job queued for processing";
      case 'started':
        return "Starting image analysis";
      case 'detecting':
        return "Detecting clothing items in image";
      case 'labelling':
        return "Generating semantic labels";
      case 'querying':
        return "Searching for similar products";
      case 'completed':
        return "Analysis complete!";
      case 'failed':
        return "Job failed - please try again";
      default:
        return "Processing...";
    }
  };

  const renderResults = () => {
    if (!jobStatus?.result || jobStatus.status !== 'completed') return null;

    const result = jobStatus.result as unknown as QueryResult;
    if (result.type !== 'querying') return null;

    return (
      <div className="mt-6">
        <h3 className="text-xl font-semibold text-[#0F172A] mb-4">Query Results</h3>
        <div className="space-y-4">
          {result.cloths?.map((cloth: ClothResult, index: number) => (
            <Card key={index} className="border-l-4 border-l-[#1F6F8B]">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Clothing Item {index + 1}</CardTitle>
              </CardHeader>
              <CardContent>
                {cloth.matched_images?.length > 0 ? (
                  <div className="space-y-3">
                    <p className="text-sm text-[#6B7280]">
                      Found {cloth.matched_images.length} similar products:
                    </p>
                    {cloth.matched_images.map((match: ClothMatch, matchIndex: number) => (
                      <div key={matchIndex} className="bg-gray-50 rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            {match.product_name && (
                              <p className="font-medium text-[#0F172A]">
                                {match.product_name}
                              </p>
                            )}
                            {match.product_description && (
                              <p className="text-sm text-[#6B7280] mt-1">
                                {match.product_description}
                              </p>
                            )}
                          </div>
                          <div className="text-right">
                            <span className="inline-block bg-[#C99B6A] text-white text-xs px-2 py-1 rounded-full">
                              {Math.round(match.score * 100)}% match
                            </span>
                            <p className="text-xs text-[#6B7280] mt-1">
                              Rank: {match.rank}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[#6B7280]">No similar products found for this clothing item.</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className={FASHION_THEME.spacing.container}>
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#0F172A]">Find Similar Clothing</h1>
          <p className="text-[#6B7280] mt-2 max-w-2xl mx-auto">
            Upload an image containing clothing items and our AI will detect them and find 
            visually similar products from your indexed catalog.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Image Upload Section */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center">
                <ImageIcon className="w-5 h-5 mr-2 text-[#1F6F8B]" />
                Upload Image
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* File Input */}
                <div>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-[#1F6F8B] file:text-white hover:file:bg-[#1A5A6F]"
                  />
                  <p className="text-xs text-[#6B7280] mt-2">
                    Supported formats: JPEG, PNG. Maximum size: 10MB
                  </p>
                </div>

                {/* Image Preview */}
                {previewUrl && (
                  <div className="text-center">
                    <div className="inline-block border-2 border-gray-200 rounded-lg p-2">
                      <img
                        src={previewUrl}
                        alt="Preview"
                        className="max-w-full max-h-64 rounded object-contain"
                      />
                    </div>
                  </div>
                )}

                {/* Query Button */}
                <div className="text-center">
                  <Button
                    onClick={handleQueryImage}
                    disabled={!selectedImage || queryingJobMutation.isPending}
                    size="lg"
                    className="bg-[#1F6F8B] hover:bg-[#1A5A6F] text-white px-8 py-3"
                  >
                    <Search className="w-5 h-5 mr-2" />
                    {queryingJobMutation.isPending ? "Starting Query..." : "Find Similar Products"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Job Status */}
          {currentJobId && jobStatus && (
            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="flex items-center">
                  {getJobStatusIcon()}
                  <span className="ml-2">Job Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-[#6B7280]">Status:</span>
                    <span className="text-sm font-medium text-[#0F172A] capitalize">
                      {jobStatus.status}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-[#6B7280]">Message:</span>
                    <span className="text-sm text-[#0F172A]">
                      {getJobStatusText()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-[#6B7280]">Job ID:</span>
                    <span className="text-sm font-mono text-[#0F172A]">
                      {currentJobId}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results */}
          {renderResults()}
        </div>
      </div>
    </div>
  );
}

export default QueryPage; 