"use client";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

import { useRouter } from "next/navigation";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import Stats from "@/components/stats";
import { Input } from "@/components/ui/input";

import { v4 as uuidv4 } from "uuid"; // Add UUID library
import Loader from "@/components/loader";

type ProcessedLog = {
  ProcessId: number;
  LogId: number;
  Sentiment: number | null;
  Resolved: boolean;
  DateCreated: string; // ISO string
  LogContent: string;
  MachineName: string;
};

type ConversationResponse = {
  ConversationId: number;
  LogId: number;
};

export default function Home() {
  const router = useRouter(); // For navigation
  const [logs, setLogs] = useState<ProcessedLog[]>([]); // Store logs from the API
  const [machines, setMachines] = useState<string[]>([]); // Machine names for the dropdown
  const [totalErrors, setTotalErrors] = useState(0); // Total errors
  const [resolvedErrors, setResolvedErrors] = useState(0); // Resolved errors
  const [loading, setLoading] = useState(true); // Loading state for table
  const [navigating, setNavigating] = useState(false); // Loading state for navigation

  // Filters
  const [selectedMachine, setSelectedMachine] = useState<string | null>(null);
  const [resolvedFilter, setResolvedFilter] = useState<boolean | null>(null);
  const [dateFrom, setDateFrom] = useState<Date | null>(null);
  const [dateTo, setDateTo] = useState<Date | null>(null);

  // Fetch logs and machine names from the backend API
  useEffect(() => {
    const fetchLogsAndMachines = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/errors?sentiment=1"
        );
        if (!response.ok) {
          throw new Error("Failed to fetch logs");
        }
        const data: ProcessedLog[] = await response.json();
        console.log("Fetched logs:", data);

        // Update state with logs
        setLogs(data);

        // Extract unique machine names
        const uniqueMachines = Array.from(
          new Set(data.map((log) => log.MachineName))
        );
        setMachines(uniqueMachines);

        // Calculate total errors and resolved errors
        setTotalErrors(data.length);
        setResolvedErrors(data.filter((log) => log.Resolved).length);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    fetchLogsAndMachines();
  }, []);

  const handleNavigateToChat = async (logId: number) => {
    setNavigating(true); // Start loading during navigation
    try {
      // 1. Check if ConversationId already exists for the LogId
      const existingConversationResponse = await fetch(
        `http://127.0.0.1:8000/api/chat/conversation/log/${logId}`
      );

      if (!existingConversationResponse.ok) {
        throw new Error("Failed to check for existing conversation");
      }

      const existingConversation: ConversationResponse | null =
        await existingConversationResponse.json();

      // 2. If ConversationId exists, navigate to the conversation page
      if (existingConversation?.ConversationId) {
        router.push(`/${existingConversation.ConversationId}`);
        return;
      }

      // 3. If no ConversationId exists, fetch log content from /api/errors/
      const logResponse = await fetch(
        `http://127.0.0.1:8000/api/errors?logId=${logId}`
      );

      if (!logResponse.ok) {
        throw new Error("Failed to fetch log content");
      }

      const logs: ProcessedLog[] = await logResponse.json();
      const logData = logs.find((log) => log.LogId === logId);

      if (!logData) {
        throw new Error("Log not found");
      }

      // 4. Prepare the initial error message (conversation creation requires at least one message)
      const initialErrorMessage = {
        SentDate: new Date().toISOString(),
        Role: 1, // User message
        Content: `**I encountered an error**: ${logData.LogContent}`,
        MessageId: uuidv4(),
        ConversationId: undefined, // Will be assigned by the server
      };

      // 5. Create a new conversation with the initial error message
      const newConversationResponse = await fetch(
        `http://127.0.0.1:8000/api/chat/conversation/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            logId: logId,
            messages: [initialErrorMessage],
          }),
        }
      );

      if (!newConversationResponse.ok) {
        throw new Error("Failed to create new conversation");
      }

      const newConversation: ConversationResponse =
        await newConversationResponse.json();
      const conversationId = newConversation.ConversationId.toString();

      // 6. Generate solution using the log content with the obtained conversationId
      const solutionResponse = await fetch(
        `http://127.0.0.1:8000/api/chat/solution`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            log_content: logData.LogContent.replace(/\./g, ""),
            conversation_id: conversationId, // Use the server-assigned conversationId
          }),
        }
      );

      if (!solutionResponse.ok) {
        throw new Error("Failed to fetch solution");
      }

      const solutionData = await solutionResponse.json();

      // 7. Prepare the solution message
      const solutionMessage = {
        SentDate: new Date().toISOString(),
        Role: 0,
        Content: `**For the problem:** ${
          logData.LogContent
        }  \n**Solution we found:** ${
          solutionData.knownError === true
            ? solutionData.solution
            : solutionData.generatedSolution
        }`,
        MessageId: uuidv4(),
        ConversationId: conversationId,
      };

      // 8. Update the conversation with the solution message
      const updateConversationResponse = await fetch(
        `http://127.0.0.1:8000/api/chat/conversation/${conversationId}/messages`,
        {
          method: "PUT", // Changed from PATCH to PUT
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify([solutionMessage]),
        }
      );

      if (!updateConversationResponse.ok) {
        throw new Error("Failed to update conversation with solution");
      }

      console.log(solutionMessage);

      // 9. Preload both messages into LLM history
      const llmPreloadResponse = await fetch(
        "http://localhost:8001/preload-history",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversationId,
            messages: [
              {
                SentDate: initialErrorMessage.SentDate,
                Role: initialErrorMessage.Role,
                Content: initialErrorMessage.Content,
              },
              {
                SentDate: solutionMessage.SentDate,
                Role: solutionMessage.Role,
                Content: solutionMessage.Content,
              },
            ],
          }),
        }
      );

      if (!llmPreloadResponse.ok) {
        console.warn("Failed to preload LLM history");
      }

      // 10. Navigate to the new conversation page
      router.push(`/${conversationId}`);
    } catch (error) {
      console.error("Error navigating to chat page:", error);
    } finally {
      setNavigating(false); // Stop loading after navigation or error
    }
  };

  // Handle toggle for Resolved status
  const handleToggleResolved = async (
    processId: number,
    currentResolved: boolean
  ) => {
    try {
      // Optimistically update the UI
      setLogs((prevLogs) =>
        prevLogs.map((log) =>
          log.ProcessId === processId
            ? { ...log, Resolved: !currentResolved }
            : log
        )
      );

      // Send PATCH request to update resolved status in the backend
      const response = await fetch(
        `http://127.0.0.1:8000/api/errors/${processId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ resolved: !currentResolved }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update resolved status");
      }

      const result = await response.json();
      console.log(result.message); // Log success message
    } catch (error) {
      console.error(error);

      // Revert optimistic update if the request fails
      setLogs((prevLogs) =>
        prevLogs.map((log) =>
          log.ProcessId === processId
            ? { ...log, Resolved: currentResolved }
            : log
        )
      );
    }
  };

  // Handle search functionality
  const handleSearch = async () => {
    try {
      const params = new URLSearchParams();

      if (selectedMachine) params.append("machine_name", selectedMachine);
      if (resolvedFilter !== null)
        params.append("resolved", String(resolvedFilter));
      if (dateFrom) params.append("date_from", dateFrom.toISOString());
      if (dateTo) params.append("date_to", dateTo.toISOString());

      const response = await fetch(
        `http://127.0.0.1:8000/api/errors?${params.toString()}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch filtered logs");
      }

      const data: ProcessedLog[] = await response.json();
      console.log("Filtered logs:", data);

      // Update state with filtered logs
      setLogs(data);

      // Update stats
      setTotalErrors(data.length);
      setResolvedErrors(data.filter((log) => log.Resolved).length);
    } catch (error) {
      console.error(error);
    }
  };

  if (loading) {
    return <Loader />;
  }

  if (navigating) {
    return <Loader text="generating solution for you ..." />;
  }

  // Clear Filters Function
  const handleClearFilters = async () => {
    // Reset all filter states
    setSelectedMachine(null);
    setResolvedFilter(null);
    setDateFrom(null);
    setDateTo(null);

    // Make a request to fetch all logs (no filters applied)
    try {
      setLoading(true); // Set loading while fetching data
      const response = await fetch(
        "http://127.0.0.1:8000/api/errors?sentiment=1"
      );
      if (!response.ok) {
        throw new Error("Failed to fetch logs");
      }
      const data: ProcessedLog[] = await response.json();

      // Update state with all logs
      setLogs(data);

      // Update stats
      setTotalErrors(data.length);
      setResolvedErrors(data.filter((log) => log.Resolved).length);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col p-4 sm:p-6 md:p-8 lg:p-10 gap-10 max-w-full">
      <div className="flex justify-between items-center">
        {/* Filters Section */}
        <div className="flex flex-col gap-3">
          <h1 className="text-left text-3xl sm:text-4xl md:text-5xl font-bold text-primaryGreen">
            Solution Finding System
          </h1>
          <div className="flex flex-wrap gap-4 items-center justify-center sm:justify-start">
            {/* Machine Filter */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  className="flex cursor-pointer items-center gap-2"
                >
                  {selectedMachine || "Machine"}
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {machines.map((machine) => (
                  <DropdownMenuItem
                    key={machine}
                    onClick={() => setSelectedMachine(machine)}
                  >
                    {machine}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Date Range Filter */}
            <div className="flex gap-2 items-center flex-wrap">
              <label
                htmlFor="from-date"
                className="text-sm font-medium text-gray-700"
              >
                From:
              </label>
              <Input
                id="from-date"
                type="date"
                value={dateFrom ? dateFrom.toISOString().split("T")[0] : ""}
                onChange={(e) =>
                  setDateFrom(e.target.value ? new Date(e.target.value) : null)
                }
                placeholder="From"
                className="cursor-pointer w-auto"
              />

              <label
                htmlFor="to-date"
                className="text-sm font-medium text-gray-700"
              >
                To:
              </label>
              <Input
                id="to-date"
                type="date"
                value={dateTo ? dateTo.toISOString().split("T")[0] : ""}
                onChange={(e) =>
                  setDateTo(e.target.value ? new Date(e.target.value) : null)
                }
                placeholder="To"
                className="cursor-pointer w-auto"
              />

              {/* Resolved Filter */}
              <label
                htmlFor="resolved"
                className="text-sm font-medium text-gray-700"
              >
                Resolved:
              </label>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    id="resolved"
                    variant="outline"
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    {resolvedFilter === true
                      ? "Resolved"
                      : resolvedFilter === false
                      ? "Unresolved"
                      : "All"}
                    <ChevronDown className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  <DropdownMenuItem onClick={() => setResolvedFilter(null)}>
                    All
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setResolvedFilter(true)}>
                    Resolved
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setResolvedFilter(false)}>
                    Unresolved
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                variant="default"
                className="bg-primaryBlue cursor-pointer"
                onClick={handleSearch}
              >
                Search
              </Button>
              <Button
                variant="outline"
                className="bg-grey text-black cursor-pointer"
                onClick={handleClearFilters}
              >
                Clear
              </Button>
            </div>
          </div>
        </div>
        <Stats totalError={totalErrors} resolved={resolvedErrors} />
      </div>

      {/* Table Section */}
      <div className="w-full max-w-full max-h-[60vh] overflow-y-auto overflow-x-auto rounded-lg border border-gray-300">
        <Table className="w-full text-sm table-fixed">
          <TableHeader>
            <TableRow className="bg-primaryGreen text-white font-bold hover:bg-primaryGreen">
              <TableHead className="px-4 py-2 border border-white text-white font-bold w-5/10">
                Error
              </TableHead>
              <TableHead className="px-4 py-2 border border-white text-white font-bold w-2/10">
                Machine
              </TableHead>
              <TableHead className="px-4 py-2 border border-white text-white font-bold w-2/10">
                Date Created
              </TableHead>
              <TableHead className="px-4 py-2 border border-white text-white font-bold w-1/10">
                Resolved
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.ProcessId} className="bg-gray-100">
                <TableCell
                  className="font-medium px-4 py-2 cursor-pointer border border-gray-300 hover:bg-primaryBlue hover:text-white whitespace-normal text-wrap"
                  onClick={() => handleNavigateToChat(log.LogId)}
                  role="button"
                  aria-label={`Navigate to conversation for log ID ${log.LogId}`}
                >
                  {log.LogContent}
                </TableCell>
                <TableCell className="px-4 py-2 border border-gray-300 truncate">
                  {log.MachineName}
                </TableCell>
                <TableCell className="px-4 py-2 border border-gray-300 truncate">
                  {new Date(log.DateCreated).toLocaleDateString()}
                </TableCell>
                <TableCell className="px-4 py-2 border border-gray-300">
                  <Switch
                    className="data-[state=checked]:bg-primaryBlue data-[state=unchecked]:bg-darkGrey"
                    checked={log.Resolved}
                    onCheckedChange={() =>
                      handleToggleResolved(log.ProcessId, log.Resolved)
                    }
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
