"use client"

import {
    HeaderGroup,
    flexRender,
    getCoreRowModel,
    useReactTable,
} from "@tanstack/react-table";

import {
    Table,
    TableBody,
    TableCell,
    TableFooter,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { useTranslations } from "next-intl";
import PaginationTable from "../pagination-table/PaginationTable";
import { ActionTableProps } from "@/interfaces/table";

const ActionTable : React.FC<ActionTableProps> = ({ columns, data, pagination }) => {
    const t = useTranslations();

    const { items } = data;
    
    const table = useReactTable({
        data: items,
        columns,
        getCoreRowModel: getCoreRowModel(),
    })

    if (!items) return null

    return (
        <div className="rounded-md border border-border dark:border-darkBorder text-black dark:text-white">
            <Table>
                <TableHeader>
                    {table.getHeaderGroups().map((headerGroup: HeaderGroup<any>) => (
                        <TableRow key={headerGroup.id}>
                            {headerGroup.headers.map((header: any) => {
                                return (
                                    <TableHead key={header.id} className={header.column.columnDef.header === t('table.headers.actions')? "text-center" : ""}>
                                        {header.isPlaceholder
                                            ? null
                                            : flexRender(
                                                header.column.columnDef.header,
                                                header.getContext()
                                            )}
                                    </TableHead>
                                )
                            })}
                        </TableRow>
                    ))}
                </TableHeader>
                <TableBody>
                    {table.getRowModel() && table.getRowModel().rows && table.getRowModel().rows.length > 0 ? (
                        table.getRowModel().rows.map((row : any) => (
                            <TableRow
                                key={row.id}
                                data-state={row.getIsSelected() && "selected"}
                            >
                                {row.getVisibleCells().map((cell : any) => (
                                    <TableCell key={cell.id}>
                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </TableCell>
                                ))}
                            </TableRow>
                        ))
                    ) : (
                        <TableRow>
                            <TableCell colSpan={columns.length + 1} className="h-24 text-center">
                                {t("table.messages.no_results")}
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
                {pagination ?
                    <TableFooter>
                        <TableRow>
                            <TableCell colSpan={columns.length + 1}>
                                <PaginationTable {...data} />
                            </TableCell>
                        </TableRow>
                    </TableFooter>
                    : 
                    null
                }
            </Table>
        </div>
    )
}

export default ActionTable;
