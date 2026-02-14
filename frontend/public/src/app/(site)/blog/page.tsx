import Link from "next/link";
import Image from "next/image";
import { Container } from "@/components/layout";
import { ArrowRight, Calendar } from "lucide-react";
import { fetchBlogPosts, fetchBlogCategories } from "@/lib/api/client";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Blog & Medya | Gastrotech",
  description: "Endüstriyel mutfak sektörü haberleri, trendler ve ipuçları.",
};

export const revalidate = 600; // Revalidate every 10 minutes

export default async function BlogPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string; page?: string }>;
}) {
  // Await searchParams properly
  const { category, page } = await searchParams;

  // Fetch data in parallel
  const [postsData, categories] = await Promise.all([
    fetchBlogPosts({
      category,
      page: page ? parseInt(page) : 1,
      page_size: 9
    }),
    fetchBlogCategories(),
  ]);

  const posts = postsData.results;

  return (
    <>
      {/* Header */}
      <section className="bg-muted/30 py-16 lg:py-20">
        <Container className="text-center">
          <h1 className="text-3xl font-bold lg:text-5xl">Blog & Medya</h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
            Sektör haberleri, ipuçları ve endüstriyel mutfak dünyasından güncel içerikler
          </p>
        </Container>
      </section>

      {/* Category Filter */}
      <section className="border-b">
        <Container>
          <div className="flex justify-center gap-2 overflow-x-auto py-4">
            <Link
              href="/blog"
              className={`whitespace-nowrap rounded-sm px-4 py-2 text-sm font-medium transition-colors ${!category
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80"
                }`}
            >
              Tümü
            </Link>
            {categories.map((cat) => (
              <Link
                key={cat.id}
                href={`/blog?category=${cat.slug}`}
                className={`whitespace-nowrap rounded-sm px-4 py-2 text-sm font-medium transition-colors ${category === cat.slug
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted hover:bg-muted/80"
                  }`}
              >
                {cat.name_tr}
              </Link>
            ))}
          </div>
        </Container>
      </section>

      {/* Blog Posts */}
      <section className="py-12 lg:py-16">
        <Container>
          {posts.length > 0 ? (
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {posts.map((post) => (
                <article
                  key={post.id}
                  className="group flex flex-col overflow-hidden rounded-sm border bg-card transition-shadow hover:shadow-lg"
                >
                  {/* Image */}
                  <div className="relative aspect-[16/10] overflow-hidden bg-muted">
                    {post.cover_url ? (
                      <Image
                        src={post.cover_url}
                        alt={post.title}
                        fill
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                        className="object-cover transition-transform duration-300 group-hover:scale-105"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-muted-foreground bg-secondary">
                        <span className="text-sm">Görsel Yok</span>
                      </div>
                    )}
                    {post.category && (
                      <div className="absolute left-3 top-3">
                        <span className="rounded-sm bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
                          {post.category.name_tr}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex flex-1 flex-col p-6">
                    <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {post.published_at ? new Date(post.published_at).toLocaleDateString("tr-TR", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      }) : "Tarih yok"}
                    </div>
                    <h2 className="mb-2 text-lg font-semibold group-hover:text-primary line-clamp-2">
                      <Link href={`/blog/${post.slug}`}>{post.title}</Link>
                    </h2>
                    <p className="mb-4 flex-1 text-sm text-muted-foreground line-clamp-3">
                      {post.excerpt}
                    </p>
                    <Link
                      href={`/blog/${post.slug}`}
                      className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                    >
                      Devamını Oku
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-lg text-muted-foreground">Bu kategoride henüz yazı bulunmuyor.</p>
              <Link href="/blog" className="mt-4 inline-block text-primary hover:underline">
                Tüm yazıları gör
              </Link>
            </div>
          )}

          {/* Load More (Pagination) - Simplified for now */}
          {postsData.next && (
            <div className="mt-12 text-center">
              <Link
                href={`/blog?${new URLSearchParams({ ...(category ? { category } : {}), page: ((page ? parseInt(page) : 1) + 1).toString() }).toString()}`}
                className="rounded-sm border bg-card px-6 py-3 font-medium transition-colors hover:bg-muted inline-block"
              >
                Sonraki Sayfa
              </Link>
            </div>
          )}
        </Container>
      </section>

      {/* Newsletter */}
      <section className="border-t bg-muted/30 py-12">
        <Container>
          <div className="mx-auto max-w-xl text-center">
            <h2 className="text-xl font-bold">Bültenimize Abone Olun</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Sektör haberleri ve özel içerikler için e-posta listemize katılın.
            </p>
            <div className="mt-4 flex gap-2">
              <input
                type="email"
                placeholder="E-posta adresiniz"
                disabled
                className="flex-1 rounded-sm border bg-background px-4 py-2 text-sm opacity-60 cursor-not-allowed"
              />
              <button
                type="button"
                disabled
                className="rounded-sm bg-primary px-6 py-2 text-sm font-medium text-primary-foreground opacity-60 cursor-not-allowed"
                title="Bu özellik yakında aktif olacak"
              >
                Yakında
              </button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Bu özellik yakında aktif olacak.
            </p>
          </div>
        </Container>
      </section>
    </>
  );
}
