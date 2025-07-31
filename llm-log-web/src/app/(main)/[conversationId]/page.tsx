"use client";

import { useParams, useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import Chat from "@/components/chat";
import { Message } from "@/components/chat";
import { Button } from "@/components/ui/button"; // shadcn/ui button
import { Input } from "@/components/ui/input"; // shadcn/ui input
import { v4 as uuidv4 } from "uuid"; // Add UUID library
import { Switch } from "@/components/ui/switch";
import { ChevronLeftIcon } from "lucide-react";
import Loader from "@/components/loader";

const ConversationPage = () => {
  const router = useRouter(); // Hook for navigation
  const params = useParams();
  const conversationId = params?.conversationId; // Extract dynamic route parameter
  const [messages, setMessages] = useState<Message[]>([]); // State to store messages
  const [logData, setLogData] = useState<{
    LogId: number;
    LogContent: string;
  } | null>(null);

  const [resolved, setResolved] = useState<boolean>(false); // State to store resolved status
  const [loadingMessages, setLoadingMessages] = useState(true); // Loading state for messages
  const [loadingLog, setLoadingLog] = useState(true); // Loading state for log content
  const [error, setError] = useState<string | null>(null); // Error state
  const [newMessage, setNewMessage] = useState(""); // Input field state
  const [showModal, setShowModal] = useState(false); // Modal visibility state
  const [isLLMLoading, setIsLLMLoading] = useState(false); // New state for LLM loading
  const [solutionPending, setSolutionPending] = useState(false); // Track if solution input is pending
  // const [generatingSolution, setGeneratingSolution] = useState(false); // Track if solution is being generated
  // Fetch log content and resolved status

  // Check if solution generation should be prevented
  useEffect(() => {
    const fetchLogContentAndResolvedStatus = async () => {
      try {
        // Fetch log content
        const logResponse = await fetch(
          `http://127.0.0.1:8000/api/chat/conversation/${conversationId}/log`
        );
        if (!logResponse.ok) {
          throw new Error("Failed to fetch log content");
        }
        const logData = await logResponse.json();
        console.log("Fetched log data:", logData);
        setLogData(logData); // Set log data

        // Fetch resolved status
        const resolvedResponse = await fetch(
          `http://127.0.0.1:8000/api/chat/log/${logData.LogId}/resolved`
        );
        if (!resolvedResponse.ok) {
          throw new Error("Failed to fetch resolved status");
        }
        const resolvedData = await resolvedResponse.json();
        setResolved(resolvedData.resolved); // Set resolved status
      } catch (err) {
        console.error(err);
        setError("Failed to load log content or resolved status.");
      } finally {
        setLoadingLog(false);
      }
    };

    fetchLogContentAndResolvedStatus();
  }, [conversationId]);

  // Fetch chat messages
  useEffect(() => {
    if (!logData) {
      return; // Exit if logData is not ready
    }

    const fetchMessages = async () => {
      try {
        // Fetch messages from database
        const response = await fetch(
          `http://127.0.0.1:8000/api/chat/conversation/${conversationId}/messages`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch messages");
        }
        const data: Message[] = await response.json();
        setMessages(data);

        // Preload messages into LLM history if any exist
        if (data.length > 0) {
          const preloadResponse = await fetch(
            `http://127.0.0.1:8001/preload-history`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                conversation_id: conversationId,
                messages: data.map((msg) => ({
                  SentDate: msg.SentDate,
                  Role: msg.Role,
                  Content: msg.Content,
                })),
              }),
            }
          );
          if (!preloadResponse.ok) {
            throw new Error("Failed to preload messages into LLM history");
          }
          const preloadData = await preloadResponse.json();
          console.log("Preloaded LLM history:", preloadData);
        }
      } catch (err) {
        console.error(err);
        setError("Failed to fetch messages or preload LLM history.");
      } finally {
        setLoadingMessages(false);
      }
    };
    fetchMessages();
  }, [conversationId, logData]);

  // Toggle the resolved status
  const handleToggleResolved = async () => {
    if (!logData?.LogId) {
      console.error("Log ID not found");
      return;
    }

    try {
      // Optimistically update the UI
      const newResolved = !resolved;
      setResolved(newResolved);

      // Send PATCH request to update resolved status
      const response = await fetch(
        `http://127.0.0.1:8000/api/chat/log/${logData.LogId}/resolved`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ resolved: !resolved }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update resolved status");
      }

      const data = await response.json();
      console.log(data.message); // Log success message
      // If resolved is set to true, trigger the solution question
      if (newResolved) {
        setSolutionPending(true);
        const solutionQuestion = {
          SentDate: new Date().toISOString(),
          Role: 0,
          Content:
            "I saw that you have triggered the solved switch. **Which solution did you use**, answer **'same'** if you used the provided solution, or **else tell me the solution that you used**.",
          MessageId: uuidv4(),
          ConversationId: Number(conversationId),
        };
        setMessages((prev) => [...prev, solutionQuestion]);

        // Save the question to the backend
        await fetch(
          `http://localhost:8000/api/chat/conversation/${conversationId}/messages`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify([solutionQuestion]),
          }
        );

        // Preload the question into LLM history
        await fetch(`http://127.0.0.1:8001/preload-history`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversationId,
            messages: [
              {
                SentDate: solutionQuestion.SentDate,
                Role: solutionQuestion.Role,
                Content: solutionQuestion.Content,
              },
            ],
          }),
        });
      }
    } catch (err) {
      console.error(err);
      setError("Failed to update resolved status.");
      setResolved((prev) => !prev); // Revert optimistic update if the request fails
    }
  };

  const handleConfirmBack = () => {
    setShowModal(false); // Close the modal
    router.push("/mainerror"); // Navigate to the home page
  };

  // Handle sending a new message and process solution if pending
  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    const tempMessageId = uuidv4();
    const userMessage = {
      SentDate: new Date().toISOString(),
      Role: 1,
      Content: newMessage,
      MessageId: tempMessageId,
      ConversationId: Number(conversationId),
    };

    setMessages((prev) => [...prev, userMessage]);
    setNewMessage("");
    setIsLLMLoading(true);

    try {
      // Save user message to backend
      await fetch(
        `http://localhost:8000/api/chat/conversation/${conversationId}/messages`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify([userMessage]),
        }
      );

      // Ask LLM if not processing solution
      let llmData = null;
      if (!solutionPending) {
        const llmResponse = await fetch("http://localhost:8001/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversationId,
            query: userMessage.Content,
          }),
        });
        llmData = await llmResponse.json();
      }

      // Process solution if pending
      if (solutionPending) {
        const lastMessage = messages[messages.length - 1];
        if (
          lastMessage.Role === 0 &&
          lastMessage.Content.includes("solved switch")
        ) {
          if (newMessage.toLowerCase() === "same") {
            // Find the first AI message after the "solved switch" message
            let solutionToSave = "";
            if (
              messages.length > 1 &&
              messages[1].Role === 0 &&
              messages[1].Content.includes("\n**Solution we found:**")
            ) {
              solutionToSave = messages[1].Content.split(
                "\n**Solution we found:**"
              )[1].trim();
            }

            if (solutionToSave) {
              // Fetch machines to map machine name to MachineId
              const machinesResponse = await fetch(
                "http://localhost:8000/api/knowledgebase/machines"
              );
              const machines = await machinesResponse.json();
              const machineEntry = machines.find(
                (m: { MachineName: string }) =>
                  m.MachineName === logData?.LogContent
              );
              const machineId = machineEntry ? machineEntry.MachineId : 1; // Default to 1 if not found

              // Check if the error (logContent) exists in knowledge base
              const existsResponse = await fetch(
                `http://localhost:8000/api/knowledgebase/exists?content=${encodeURIComponent(
                  logData?.LogContent || ""
                )}`
              );
              const existsData = await existsResponse.json();

              // Update or create knowledge base entry
              let confirmationMessage;
              if (existsData.exists) {
                // Patch existing entry
                await fetch(
                  `http://localhost:8000/api/knowledgebase/${existsData.knowledge_id}`,
                  {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ solution: solutionToSave }),
                  }
                );
                confirmationMessage = {
                  SentDate: new Date().toISOString(),
                  Role: 0,
                  Content: "Update to knowledge base completed successfully.",
                  MessageId: uuidv4(),
                  ConversationId: Number(conversationId),
                };
              } else {
                // Create new entry
                const payload = {
                  Content: logData?.LogContent || "",
                  ContentType: "Guide",
                  MachineId: machineId,
                  Solution: solutionToSave,
                };
                await fetch("http://localhost:8000/api/knowledgebase", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(payload),
                });
                confirmationMessage = {
                  SentDate: new Date().toISOString(),
                  Role: 0,
                  Content: "New knowledge base entry created successfully.",
                  MessageId: uuidv4(),
                  ConversationId: Number(conversationId),
                };
              }

              setMessages((prev) => [...prev, confirmationMessage]);
              await fetch(
                `http://localhost:8000/api/chat/conversation/${conversationId}/messages`,
                {
                  method: "PUT",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify([confirmationMessage]),
                }
              );
              // Preload the confirmation message into LLM history
              await fetch(`http://127.0.0.1:8001/preload-history`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  conversation_id: conversationId,
                  messages: [
                    {
                      SentDate: confirmationMessage.SentDate,
                      Role: confirmationMessage.Role,
                      Content: confirmationMessage.Content,
                    },
                  ],
                }),
              });
            } else {
              // Fallback if no solution is found
              const fallbackMessage = {
                SentDate: new Date().toISOString(),
                Role: 0,
                Content: "No previous solution found to confirm with 'same'.",
                MessageId: uuidv4(),
                ConversationId: Number(conversationId),
              };
              setMessages((prev) => [...prev, fallbackMessage]);
              await fetch(
                `http://localhost:8000/api/chat/conversation/${conversationId}/messages`,
                {
                  method: "PUT",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify([fallbackMessage]),
                }
              );
              await fetch(`http://127.0.0.1:8001/preload-history`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  conversation_id: conversationId,
                  messages: [
                    {
                      SentDate: fallbackMessage.SentDate,
                      Role: fallbackMessage.Role,
                      Content: fallbackMessage.Content,
                    },
                  ],
                }),
              });
            }
            setSolutionPending(false); // Reset pending state
          } else {
            const solutionToSave = newMessage; // Use the new solution provided

            // Fetch machines to map machine name to MachineId
            const machinesResponse = await fetch(
              "http://localhost:8000/api/knowledgebase/machines"
            );
            const machines = await machinesResponse.json();
            const machineEntry = machines.find(
              (m: { MachineName: string }) =>
                m.MachineName === logData?.LogContent
            );
            const machineId = machineEntry ? machineEntry.MachineId : 1; // Default to 1 if not found

            // Check if the error (logContent) exists in knowledge base
            const existsResponse = await fetch(
              `http://localhost:8000/api/knowledgebase/exists?content=${encodeURIComponent(
                logData?.LogContent || ""
              )}`
            );
            const existsData = await existsResponse.json();

            // Update or create knowledge base entry
            let confirmationMessage;
            if (existsData.exists) {
              // Patch existing entry
              await fetch(
                `http://localhost:8000/api/knowledgebase/${existsData.knowledge_id}`,
                {
                  method: "PATCH",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ solution: solutionToSave }),
                }
              );
              confirmationMessage = {
                SentDate: new Date().toISOString(),
                Role: 0,
                Content: "Update to knowledge base completed successfully.",
                MessageId: uuidv4(),
                ConversationId: Number(conversationId),
              };
            } else {
              // Create new entry
              const payload = {
                Content: logData?.LogContent || "",
                ContentType: "Guide",
                MachineId: machineId,
                Solution: solutionToSave,
              };
              await fetch("http://localhost:8000/api/knowledgebase", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              });
              confirmationMessage = {
                SentDate: new Date().toISOString(),
                Role: 0,
                Content: "New knowledge base entry created successfully.",
                MessageId: uuidv4(),
                ConversationId: Number(conversationId),
              };
            }

            setMessages((prev) => [...prev, confirmationMessage]);
            await fetch(
              `http://localhost:8000/api/chat/conversation/${conversationId}/messages`,
              {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify([confirmationMessage]),
              }
            );
            // Preload the confirmation message into LLM history
            await fetch(`http://127.0.0.1:8001/preload-history`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                conversation_id: conversationId,
                messages: [
                  {
                    SentDate: confirmationMessage.SentDate,
                    Role: confirmationMessage.Role,
                    Content: confirmationMessage.Content,
                  },
                ],
              }),
            });
            setSolutionPending(false); // Reset pending state
          }
        }
      }

      // Handle LLM response if not processing solution
      if (!solutionPending && llmData) {
        const assistantMessage = {
          SentDate: new Date().toISOString(),
          Role: 0,
          Content: llmData.answer,
          MessageId: uuidv4(),
          ConversationId: Number(conversationId),
        };

        setMessages((prev) => [...prev, assistantMessage]);

        await fetch(
          `http://localhost:8000/api/chat/conversation/${conversationId}/messages`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify([assistantMessage]),
          }
        );
        // Preload the assistant message into LLM history
        await fetch(`http://127.0.0.1:8001/preload-history`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversationId,
            messages: [
              {
                SentDate: assistantMessage.SentDate,
                Role: assistantMessage.Role,
                Content: assistantMessage.Content,
              },
            ],
          }),
        });
      }
    } catch (err) {
      console.error("Error sending message:", err);
    } finally {
      setIsLLMLoading(false);
    }
  };

  // Handle Enter key press to send message
  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault(); // Correct method to prevent default behavior
      handleSendMessage(); // Trigger send message
    }
  };
  if (loadingMessages || loadingLog) {
    return <Loader />;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className=" flex flex-col p-10 gap-3 max-h-screen">
      <div className="gap-1">
        <Button
          className="bg-primaryRed text-white w-fit"
          onClick={() => setShowModal(true)}
        >
          <ChevronLeftIcon />
          Back
        </Button>
        <h1 className="text-left text-[50px] font-bold mb- text-primaryGreen">
          Chat With Me Free Solution
        </h1>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="max-h-screen fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-bold mb-4">
              Confirm Going Back To Home Page
            </h2>
            <p className="mb-6">Are you sure you want to go back?</p>
            <div className="flex justify-end gap-4">
              <Button
                className="bg-primaryRed text-white"
                onClick={() => setShowModal(false)}
              >
                Cancel
              </Button>
              <Button
                className="bg-primaryBlue text-white"
                onClick={handleConfirmBack}
              >
                Confirm
              </Button>
            </div>
          </div>
        </div>
      )}
      {/* Log Content */}
      <div className=" flex items-center justify-between gap-4">
        {logData?.LogContent && (
          <p className="text-black font-bold text-[20px] flex-1">
            {logData.LogContent}
          </p>
        )}
        <label className="Label" htmlFor="resolved">
          Resolved?
        </label>
        <Switch
          id="resolved"
          checked={resolved}
          onCheckedChange={handleToggleResolved}
          className="data-[state=checked]:bg-primaryBlue data-[state=unchecked]:bg-darkGrey"
        />
      </div>
      <div className=" flex-grow">
        <Chat
          messages={[
            ...messages,
            ...(isLLMLoading
              ? [
                  {
                    SentDate: new Date().toISOString(),
                    Role: 0,
                    Content: "Loading...", // Display loading text
                    MessageId: "loading-" + uuidv4(),
                    ConversationId: Number(conversationId),
                    isLoading: true, // Optional flag to style loading bubble
                  },
                ]
              : []),
          ]}
        />

        <div className="pt-3 border-t flex items-center gap-2">
          <Input
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-grow"
            onKeyDown={handleKeyPress} // Add key press handler
            disabled={loadingMessages}
          />
          <Button
            className="bg-primaryBlue"
            onClick={handleSendMessage}
            disabled={newMessage == ""}
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ConversationPage;
