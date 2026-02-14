"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, AlertCircle, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card";
import { useLogin } from "@/hooks/use-auth";
import { toast } from "@/hooks/use-toast";
import { TokenStore, checkBackendHealth } from "@/lib/api";

const loginSchema = z.object({
  email: z.string().email("Geçerli bir e-posta adresi giriniz"),
  password: z.string().min(1, "Şifre gereklidir"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const loginMutation = useLogin();
  const hasCheckedAuth = useRef(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // Check once on mount if already logged in
  useEffect(() => {
    if (hasCheckedAuth.current) return;
    hasCheckedAuth.current = true;

    // Only redirect if we have valid tokens
    if (TokenStore.hasTokens()) {
      router.replace("/dashboard");
      return;
    }

    // Backend health check - console log only (DEV)
    if (process.env.NODE_ENV === "development") {
      checkBackendHealth().then((status) => {
        console.log("[Login] Backend health:", status);
      });
    }
  }, [router]);

  const onSubmit = async (data: LoginFormData) => {
    setLoginError(null);

    try {
      await loginMutation.mutateAsync(data);
      toast({
        title: "Giriş başarılı",
        description: "Yönetim paneline yönlendiriliyorsunuz...",
        variant: "success",
      });
      router.replace("/dashboard");
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "E-posta veya şifre hatalı. Lütfen tekrar deneyiniz.";

      setLoginError(message);
      toast({
        title: "Giriş başarısız",
        description: message,
        variant: "destructive",
      });
    }
  };

  const isDev = process.env.NODE_ENV === "development";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-stone-50 via-white to-stone-100 p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent pointer-events-none" />

      <Card className="w-full max-w-md border-stone-200 shadow-xl relative card-elevated rounded-sm">
        <CardHeader className="text-center pb-6 pt-12">
          {/* Logo - Single big image only */}
          {/* Logo - Single big image only */}
          <div className="flex justify-center">
            {/* Using standard img tag to avoid Next.js Image optimization issues with basePath */}
            <img
              src="/admin/brand/logo.png"
              alt="GastroTech"
              className="w-[140px] sm:w-[170px] md:w-[200px] h-auto object-contain"
            />
          </div>
        </CardHeader>

        <CardContent className="pb-8 pt-2">
          {/* Login Error Display */}
          {loginError && (
            <div className="mb-4 p-3 rounded-sm text-sm bg-red-50 text-red-700 border border-red-200 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-stone-700">
                E-posta
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@gastrotech.com"
                autoComplete="email"
                className="h-11 rounded-sm"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-xs text-destructive mt-1">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-stone-700">
                Şifre
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                className="h-11 rounded-sm"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-xs text-destructive mt-1">{errors.password.message}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full h-12 text-base font-semibold rounded-sm"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Giriş yapılıyor...
                </>
              ) : (
                "Giriş Yap"
              )}
            </Button>
          </form>

          {/* Dev hint */}
          {isDev && (
            <p className="mt-5 text-xs text-stone-400 text-center">
              Dev: admin@gastrotech.com / admin123
            </p>
          )}
        </CardContent>
      </Card>

      {/* Security footer */}
      <div className="mt-8 flex items-center gap-2 text-xs text-stone-400">
        <Shield className="h-3.5 w-3.5" />
        <span>Güvenli bağlantı ile korunmaktadır</span>
      </div>

      {/* Copyright */}
      <p className="mt-3 text-xs text-stone-400">
        © {new Date().getFullYear()} GastroTech. Tüm hakları saklıdır.
      </p>
    </div>
  );
}
