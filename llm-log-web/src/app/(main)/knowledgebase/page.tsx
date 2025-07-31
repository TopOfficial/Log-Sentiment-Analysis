"use client";
import { Button } from "@/components/ui/button";
import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Combobox } from "@/components/ui/Combobox"; // Custom or implementable
import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
  VisibilityState,
} from "@tanstack/react-table";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ArrowUpDown, ChevronDown, Plus } from "lucide-react";

import Loader from "@/components/loader";

// Type for the API response
type ApiResponse = {
  KnowledgeId: number;
  Content: string;
  MachineId: number;
  MachineName: string;
  Solution: string;
  ContentType: string;
};

// Existing frontend type
type Solution = {
  id: number; // Maps from KnowledgeId
  content: string; // Maps from Content
  machineid: number;
  machine: string; // Maps from MachineName
  solution: string; // Maps from Solution
  contentType: string;
};

const columns: ColumnDef<Solution>[] = [
  {
    accessorKey: "content",
    header: "Error Description",
  },
  {
    accessorKey: "machine",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="font-bold hover:text-white hover:bg-primaryGreen cursor-pointer"
        >
          Machine
          <ArrowUpDown />
        </Button>
      );
    },
    cell: ({ row }) => <div>{row.getValue("machine")}</div>,
    filterFn: (row, columnId, filterValue) => {
      // Match any of the selected machines
      return filterValue.includes(row.getValue(columnId));
    },
  },
  {
    accessorKey: "solution",
    header: "Solution",
  },
];

export default function KnowledgeBase() {
  const [tableData, setTableData] = useState<Solution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [selectedMachines, setSelectedMachines] = useState<string[]>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [open, setOpen] = useState(false);
  // Simulated options
  const errors = [...new Set(tableData.map((row) => row.content))];
  const solutions = [...new Set(tableData.map((row) => row.solution))];
  console.log(solutions);

  const [machinesList, setMachinesList] = useState<
    { MachineId: number; MachineName: string }[]
  >([]);
  const machines = machinesList.map((m) => m.MachineName);

  const fetchMachines = async () => {
    try {
      const response = await axios.get(
        "http://localhost:8000/api/knowledgebase/machines"
      );
      setMachinesList(response.data);
    } catch (err) {
      console.error("Error fetching machines:", err);
      setError("Failed to fetch machines.");
    }
  };

  const findExistingErrorEntry = (errorContent: string) => {
    return tableData.find((entry) => entry.content === errorContent);
  };

  // const [isModalOpen, setIsModalOpen] = useState(false); // Manage modal visibility

  // const openModal = () => setIsModalOpen(true);
  // const closeModal = () => setIsModalOpen(false);
  const fetchData = async () => {
    setLoading(true);
    try {
      // Use the ApiResponse type for the backend response
      const response = await axios.get<ApiResponse[]>(
        "http://localhost:8000/api/knowledgebase/with_name"
      );

      // Map the backend response (ApiResponse) to the frontend-friendly Solution type
      const mappedData: Solution[] = response.data.map((item) => ({
        id: item.KnowledgeId, // Map KnowledgeId to id
        content: item.Content, // Map Content to content
        machineid: item.MachineId,
        machine: item.MachineName, // Map MachineName to machine
        solution: item.Solution, // Map Solution directly
        contentType: item.ContentType,
      }));

      // Set the mapped data to the state
      setTableData(mappedData);
    } catch (err) {
      console.error("Error fetching data:", err); // Log errors for debugging
      setError("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachines();
    fetchData();
  }, []);

  const table = useReactTable({
    data: tableData,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
    },
  });

  const toggleMachineSelection = (machine: string) => {
    setSelectedMachines((prev) =>
      prev.includes(machine)
        ? prev.filter((m) => m !== machine)
        : [...prev, machine]
    );
  };

  useEffect(() => {
    // Set undefined if no machines are selected to clear the filter
    table
      .getColumn("machine")
      ?.setFilterValue(
        selectedMachines.length > 0 ? selectedMachines : undefined
      );
  }, [selectedMachines, table]);

  const [formData, setFormData] = useState({
    machine: "",
    error: "",
    solution: "",
  });

  const handleFormChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    try {
      console.log(machinesList);
      const { machine, error, solution } = formData;

      // Validate inputs
      if (!machine || !error.trim() || !solution.trim()) {
        alert("Please fill in all fields.");
        return;
      }

      // Map machine name to MachineId using machinesList
      const machineEntry = machinesList.find(
        (entry) => entry.MachineName === machine
      );
      if (!machineEntry) {
        alert("Please select a valid machine.");
        return;
      }
      const machineId = machineEntry.MachineId;

      // Check if error already exists
      const existingErrorEntry = findExistingErrorEntry(error);

      let response;

      if (existingErrorEntry) {
        // PATCH: Update existing error's solution
        const knowledgeId = existingErrorEntry.id;
        response = await axios.patch(
          `http://localhost:8000/api/knowledgebase/${knowledgeId}`,
          { solution },
          { headers: { "Content-Type": "application/json" } }
        );
        console.log("Updated solution:", response.data);
      } else {
        // POST: Add new error
        const payload = {
          Content: error.trim(),
          ContentType: "Guide",
          MachineId: machineId,
          Solution: solution.trim(),
        };
        response = await axios.post(
          "http://localhost:8000/api/knowledgebase",
          payload,
          { headers: { "Content-Type": "application/json" } }
        );
        console.log("Created new error:", response.data);
      }

      // Refresh data and reset form
      await fetchData();
      setOpen(false);
      setFormData({ machine: "", error: "", solution: "" });
    } catch (err) {
      console.error("Error submitting form:", err);
      alert(error);
    }
  };

  if (loading) {
    return <Loader />;
  }
  if (error) return <div>{error}</div>;

  return (
    <div className="w-full min-h-screen p-10">
      <h1 className="text-left text-[50px] font-bold mb- text-primaryGreen">
        Knowledge Base
      </h1>
      <div className="flex items-center py-4">
        {/* Dropdown Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              Choose Machines <ChevronDown />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            {/* Generate unique list of machines */}
            {[...new Set(tableData.map((row) => row.machine))].map(
              (machine) => (
                <DropdownMenuCheckboxItem
                  key={machine}
                  className="capitalize"
                  checked={selectedMachines.includes(machine)}
                  onCheckedChange={() => toggleMachineSelection(machine)}
                >
                  {machine}
                </DropdownMenuCheckboxItem>
              )
            )}
            <DropdownMenuSeparator />
            <DropdownMenuCheckboxItem
              checked={selectedMachines.length === 0}
              onCheckedChange={() => setSelectedMachines([])}
            >
              Clear All
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Search Input */}
        <Input
          placeholder="Filter Errors..."
          value={(table.getColumn("content")?.getFilterValue() as string) ?? ""}
          onChange={(event) =>
            table.getColumn("content")?.setFilterValue(event.target.value)
          }
          className="max-w-sm ml-auto"
        />
      </div>

      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow
                key={headerGroup.id}
                className="bg-primaryGreen hover:bg-primaryGreen"
              >
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className="text-white font-bold">
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-end space-x-2 py-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
        </Button>
      </div>
      {/* <div className="items-center justify-end flex mt-2">
        <Button variant="outline">
          New Knowledge <Plus />
        </Button>
      </div> */}
      {/* Dialog for Adding New Knowledge */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className="text-white bg-primaryBlue">
            New Knowledge <Plus />
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add new knowledge</DialogTitle>
          </DialogHeader>

          {/* Form */}
          {/* Form */}
          <div className="space-y-4">
            <div>
              <Label className="pb-2.5">What is the Machine</Label>
              <Combobox
                options={machines}
                placeholder="Select or add machine"
                onChange={(val) => handleFormChange("machine", val || "")}
              />
            </div>

            {/* Replace Combobox with Input for Error */}
            <div>
              <Label className="pb-2.5">What is the error</Label>
              <Input
                list="error-list"
                placeholder="Select or type new error"
                value={formData.error}
                onChange={(e) => handleFormChange("error", e.target.value)}
              />
              <datalist id="error-list">
                {errors.map((error, index) => (
                  <option key={index} value={error} />
                ))}
              </datalist>
            </div>

            {/* Replace Combobox with Input for Solution */}
            <div>
              <Label className="pb-2.5">What is the solution</Label>
              <Input
                placeholder="Type an existing or new solution"
                value={formData.solution}
                onChange={(e) => handleFormChange("solution", e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <Button onClick={handleSubmit} className="bg-primaryGreen">
              Submit
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
