"use client"; // Important: Needed for useRouter

import { usePathname } from "next/navigation"; // To get current route
import { Home, GraduationCap } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import Image from "next/image";

// Menu items.
const items = [
  {
    title: "Main Error",
    url: "/mainerror",
    icon: Home,
  },
  {
    title: "Knowledge Base",
    url: "/knowledgebase",
    icon: GraduationCap,
  },
];

export function AppSidebar() {
  const pathname = usePathname(); // Get current route

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        <SidebarGroup>
          {/* Logo */}
          <div className="flex items-center justify-center mb-1">
            <Image
              src="/infineon_logo.png"
              alt="Infineon Logo"
              width={128}
              height={128}
              className="rounded-full"
              priority
            />
          </div>

          <SidebarGroupLabel>LLM Log</SidebarGroupLabel>

          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const isActive = pathname === item.url;

                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      className={`h-14 text-lg font-medium hover:bg-grey ${
                        isActive ? "bg-grey text-black" : ""
                      }`}
                    >
                      <a href={item.url}>
                        <item.icon size={24} strokeWidth={2} />
                        <span>{item.title}</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
