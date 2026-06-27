import { useQuery } from "@tanstack/react-query";
import { fetchCountries } from "../api/countries";

export function useCountries() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["countries"],
    queryFn: fetchCountries,
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });

  return { countries: data ?? [], isLoading, isError, error };
}
