type StatsProps = {
  totalError: number; // Total errors count
  resolved: number; // Number of resolved errors
};

export default function Stats({ totalError, resolved }: StatsProps) {
  return (
    <div className=" flex-row justify-end items-center">
      <div className="mb-2 bg-accentGreen text-white px-4 py-2 rounded-md font-medium border-2 border-primaryGreen">
        Total Error: <span className="font-bold">{totalError}</span>
      </div>
      <div className="flex bg-accentGreen text-white px-4 py-2 rounded-md font-medium border-2 border-primaryGreen">
        Solved: <span className="font-bold">{resolved}</span>
      </div>
    </div>
  );
}
