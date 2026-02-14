"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, CheckCircle, XCircle } from "lucide-react";
import { 
  checkAdminCapabilities, 
  clearCapabilityCache, 
  getCapabilityCache,
  type AdminCapabilities 
} from "@/lib/api/capabilities";

interface CapabilityResult {
  exists: boolean;
  status: number | null;
  error?: string;
}

export default function DebugPage() {
  const [capabilities, setCapabilities] = useState<AdminCapabilities | null>(null);
  const [rawCache, setRawCache] = useState<Record<string, CapabilityResult>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCapabilities = async () => {
    setLoading(true);
    setError(null);
    try {
      const caps = await checkAdminCapabilities();
      setCapabilities(caps);
      setRawCache(getCapabilityCache());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const refreshCapabilities = async () => {
    clearCapabilityCache();
    await loadCapabilities();
  };

  useEffect(() => {
    loadCapabilities();
  }, []);

  const capabilityList = capabilities
    ? [
        { name: "canCreateProduct", value: capabilities.canCreateProduct },
        { name: "canPatchProduct", value: capabilities.canPatchProduct },
        { name: "canDeleteProduct", value: capabilities.canDeleteProduct },
        { name: "canCreateVariant", value: capabilities.canCreateVariant },
        { name: "canPatchVariant", value: capabilities.canPatchVariant },
        { name: "canDeleteVariant", value: capabilities.canDeleteVariant },
        { name: "canBulkUpdateVariants", value: capabilities.canBulkUpdateVariants },
        { name: "canListTemplates", value: capabilities.canListTemplates },
        { name: "canApplyTemplate", value: capabilities.canApplyTemplate },
        { name: "canGenerateProducts", value: capabilities.canGenerateProducts },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-900">Debug: API Capabilities</h1>
          <p className="text-sm text-stone-500">
            Shows which admin API endpoints are available on the backend.
          </p>
        </div>
        <Button onClick={refreshCapabilities} disabled={loading} variant="outline">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-4">
            <p className="text-red-600">Error: {error}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Admin API Capabilities</CardTitle>
          <CardDescription>
            Green = endpoint exists (ViewSet registered). Red = endpoint returns 404 (missing).
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {capabilityList.map(({ name, value }) => (
                <div
                  key={name}
                  className="flex items-center justify-between p-3 bg-stone-50 rounded-lg"
                >
                  <code className="text-sm font-mono">{name}</code>
                  {value ? (
                    <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Available
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="bg-red-100 text-red-800 hover:bg-red-100">
                      <XCircle className="h-3 w-3 mr-1" />
                      Missing
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Raw HTTP Responses */}
      <Card>
        <CardHeader>
          <CardTitle>Raw Endpoint Checks</CardTitle>
          <CardDescription>
            Actual HTTP status codes from OPTIONS requests to each endpoint.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-40 w-full" />
          ) : (
            <div className="space-y-2">
              {Object.entries(rawCache).map(([key, result]) => (
                <div
                  key={key}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    result.exists ? "bg-green-50" : "bg-red-50"
                  }`}
                >
                  <div className="flex-1">
                    <code className="text-sm font-mono">{key}</code>
                    {result.error && (
                      <p className="text-xs text-stone-500 mt-1">{result.error}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono">
                      {result.status ?? "N/A"}
                    </Badge>
                    {result.exists ? (
                      <Badge className="bg-green-100 text-green-800">
                        ✓ Exists
                      </Badge>
                    ) : (
                      <Badge className="bg-red-100 text-red-800">
                        ✗ Missing
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
              {Object.keys(rawCache).length === 0 && (
                <p className="text-sm text-stone-500 italic">No checks performed yet</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Environment</CardTitle>
          <CardDescription>Frontend configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-stone-50 rounded-lg">
              <code className="text-sm font-mono">NEXT_PUBLIC_BACKEND_URL</code>
              <code className="text-sm text-stone-600">
                {process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}
              </code>
            </div>
            <div className="flex items-center justify-between p-3 bg-stone-50 rounded-lg">
              <code className="text-sm font-mono">NODE_ENV</code>
              <code className="text-sm text-stone-600">
                {process.env.NODE_ENV || "unknown"}
              </code>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>Troubleshooting</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-stone-600 space-y-2">
          <p><strong>If all capabilities show &quot;Missing&quot;:</strong></p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Check that the backend is running at the configured URL</li>
            <li>Check browser console for CORS errors</li>
            <li>Verify you&apos;re logged in with a valid token</li>
          </ul>
          <p className="mt-4"><strong>Expected status codes:</strong></p>
          <ul className="list-disc pl-5 space-y-1">
            <li><code>200</code> - Endpoint exists and OPTIONS succeeded</li>
            <li><code>401</code> - Endpoint exists but needs auth (still counts as &quot;exists&quot;)</li>
            <li><code>403</code> - Endpoint exists but permission denied (still counts as &quot;exists&quot;)</li>
            <li><code>404</code> - Endpoint does NOT exist (route not registered)</li>
            <li><code>405</code> - Endpoint exists but OPTIONS not allowed (still counts as &quot;exists&quot;)</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
