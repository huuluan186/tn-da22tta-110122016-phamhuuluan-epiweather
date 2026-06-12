import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchDiseases } from "../api/diseases";
import { DISEASE_PRESENTATION, SUPPORTED_DISEASE_IDS } from "../constants";
import type { DiseaseDef, DiseaseId } from "../types/domain";

function isDiseaseId(code: string): code is DiseaseId {
	return SUPPORTED_DISEASE_IDS.includes(code as DiseaseId);
}

const FALLBACK_DISEASES: DiseaseDef[] = SUPPORTED_DISEASE_IDS.map((id) => ({
	id,
	label: id.toUpperCase(),
	description: "",
	...DISEASE_PRESENTATION[id],
}));

export function useDiseases() {
	const query = useQuery({
		queryKey: ["diseases"],
		queryFn: fetchDiseases,
		staleTime: 30 * 60 * 1000,
		retry: 1,
	});

	const diseases = useMemo<DiseaseDef[]>(() => {
		if (!query.data) return FALLBACK_DISEASES;

		const itemsByCode = new Map(
			query.data.filter((item) => isDiseaseId(item.code)).map((item) => [item.code, item]),
		);

		return SUPPORTED_DISEASE_IDS.map((id) => {
			const item = itemsByCode.get(id);
			if (!item) return FALLBACK_DISEASES.find((disease) => disease.id === id)!;

			return {
				id,
				label: item.display_name_vi || item.display_name,
				description: item.description_vi || item.description || "",
				...DISEASE_PRESENTATION[id],
			};
		});
	}, [query.data]);

	const diseaseById = useMemo(
		() => new Map<DiseaseId, DiseaseDef>(diseases.map((disease) => [disease.id, disease])),
		[diseases],
	);

	const getDisease = (id: DiseaseId) =>
		diseaseById.get(id) ?? FALLBACK_DISEASES.find((disease) => disease.id === id)!;

	return {
		diseases,
		getDisease,
		isLoading: query.isLoading,
		isError: query.isError,
		error: query.error,
	};
}
