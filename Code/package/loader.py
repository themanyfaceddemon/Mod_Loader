from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
from .identifier import Identifier
from .metadata import IdentifierConflict, MetaData
from .package import Package


class ModLoader:
    active_mods: List[Package] = []
    inactive_mods: List[Package] = []

    @classmethod
    def _find_package_by_id(cls, package_id: str) -> Optional[Package]:
        for pkg in cls.active_mods + cls.inactive_mods:
            if pkg.identifier.id == package_id:
                return pkg
        return None

    @classmethod
    def _sort_active_mods_by_load_order(cls) -> List[Package]:
        return sorted(
            cls.active_mods,
            key=lambda pkg: (pkg.metadata.load_order is None, pkg.metadata.load_order),
        )

    @classmethod
    def _add_dependencies_from_inactive(cls) -> None:
        active_ids = {pkg.identifier.id for pkg in cls.active_mods}

        for pkg in list(cls.active_mods):
            for req in pkg.metadata.requirements:
                if req.id not in active_ids:
                    dep_pkg = cls._find_package_by_id(req.id)
                    if dep_pkg and dep_pkg in cls.inactive_mods:
                        cls.active_mods.append(dep_pkg)
                        cls.inactive_mods.remove(dep_pkg)
                        active_ids.add(dep_pkg.identifier.id)

            for patch in pkg.metadata.patches:
                if patch.id not in active_ids:
                    dep_pkg = cls._find_package_by_id(patch.id)
                    if dep_pkg and dep_pkg in cls.inactive_mods:
                        cls.active_mods.append(dep_pkg)
                        cls.inactive_mods.remove(dep_pkg)
                        active_ids.add(dep_pkg.identifier.id)

    @classmethod
    def _build_dependency_graph(cls) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        graph: Dict[str, List[str]] = defaultdict(list)
        indegree: Dict[str, int] = {pkg.identifier.id: 0 for pkg in cls.active_mods}

        def add_dependency(package_id: str, dependency_id: str) -> None:
            if dependency_id in indegree:
                graph[dependency_id].append(package_id)
                indegree[package_id] += 1

        for pkg in cls.active_mods:
            current_id = pkg.identifier.id
            for req in pkg.metadata.requirements:
                add_dependency(current_id, req.id)
            for patch in pkg.metadata.patches:
                add_dependency(patch.id, current_id)
            for opt_req in pkg.metadata.optionals_requirements:
                if opt_req.id in indegree:
                    add_dependency(current_id, opt_req.id)
            for opt_patch in pkg.metadata.optionals_patches:
                if opt_patch.id in indegree:
                    add_dependency(opt_patch.id, current_id)

        return graph, indegree

    @classmethod
    def _topological_sort(
        cls,
        graph: Dict[str, List[str]],
        indegree: Dict[str, int],
    ) -> List[Package]:
        queue: deque[str] = deque(
            [pkg_id for pkg_id, deg in indegree.items() if deg == 0]
        )
        final_sorted_packages: List[Package] = []

        while queue:
            sorted_level = sorted(
                (
                    pkg_id
                    for pkg_id in queue
                    if cls._find_package_by_id(pkg_id) is not None
                ),
                key=lambda pkg_id: cls._find_package_by_id(pkg_id).identifier.name,  # type: ignore
            )
            queue = deque(sorted_level)

            for current_id in list(queue):
                queue.popleft()
                current_pkg = cls._find_package_by_id(current_id)
                if current_pkg:
                    final_sorted_packages.append(current_pkg)
                else:
                    raise ValueError(
                        f"Package with id '{current_id}' not found in active mods or inactive mods"
                    )

                for neighbor in graph[current_id]:
                    indegree[neighbor] -= 1
                    if indegree[neighbor] == 0:
                        queue.append(neighbor)

        if len(final_sorted_packages) != len(indegree):
            raise ValueError("Unable to resolve dependencies: cycle detected.")

        return final_sorted_packages

    @classmethod
    def sort(cls) -> None:
        cls.active_mods = cls._sort_active_mods_by_load_order()
        cls._add_dependencies_from_inactive()
        graph, indegree = cls._build_dependency_graph()
        cls.active_mods = cls._topological_sort(graph, indegree)
        for index, mod in enumerate(cls.active_mods):
            mod.metadata.load_order = index + 1

    @classmethod
    def add_to_active(cls, package: Package, position: Optional[int] = None) -> None:
        if position is not None and 0 <= position < len(cls.active_mods):
            cls.active_mods.insert(position, package)
        else:
            cls.active_mods.append(package)

    @classmethod
    def remove_from_active(cls, package_id: str) -> bool:
        for pkg in cls.active_mods:
            if pkg.identifier.id == package_id:
                cls.active_mods.remove(pkg)
                return True

        return False

    @classmethod
    def remove_from_inactive(cls, package_id: str) -> bool:
        for pkg in cls.inactive_mods:
            if pkg.identifier.id == package_id:
                cls.inactive_mods.remove(pkg)
                return True

        return False

    @classmethod
    def add_to_inactive(cls, package: Package) -> None:
        if package not in cls.inactive_mods:
            cls.inactive_mods.append(package)

    @classmethod
    def find_in_active(cls, package_id: str) -> Optional[Package]:
        for pkg in cls.active_mods:
            if pkg.identifier.id == package_id:
                return pkg

        return None

    @classmethod
    def find_in_inactive(cls, package_id: str) -> Optional[Package]:
        for pkg in cls.inactive_mods:
            if pkg.identifier.id == package_id:
                return pkg

        return None
