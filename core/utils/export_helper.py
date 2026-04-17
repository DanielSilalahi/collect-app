import io
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
import openpyxl
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, Query
import pytz

class DataExporter:
    """Helper class to handle data export to Excel/CSV with efficient memory usage."""

    @staticmethod
    def format_datetime(dt: Optional[datetime], timezone: str = "Asia/Jakarta") -> str:
        if dt is None:
            return "-"
        tz = pytz.timezone(timezone)
        if dt.tzinfo is None:
            # Assume UTC if no timezone is set
            dt = pytz.utc.localize(dt)
        return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def export_to_excel(
        query: Query,
        field_mappings: List[Dict[str, Union[str, Callable[[Any], Any]]]],
        filename_prefix: str = "export",
        sheet_title: str = "Data",
        batch_size: int = 1000,
    ) -> StreamingResponse:
        """
        Exports a SQLAlchemy query results to Excel file using StreamingResponse.
        
        Args:
            query: The SQLAlchemy query to execute.
            field_mappings: A list of dicts with 'label' (header) and 'attr' (attribute name) 
                            or 'func' (callback function that takes the object).
            filename_prefix: Prefix for the generated filename.
            sheet_title: Title of the worksheet.
            batch_size: Number of records to fetch at once.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_title

        # Header
        headers = [m["label"] for m in field_mappings]
        ws.append(headers)

        # Fetch in batches
        offset = 0
        total_rows = 0
        while True:
            batch = query.offset(offset).limit(batch_size).all()
            if not batch:
                break
            
            for obj in batch:
                row = []
                for mapping in field_mappings:
                    if "func" in mapping and callable(mapping["func"]):
                        val = mapping["func"](obj)
                    else:
                        attr_chain = mapping["attr"].split(".")
                        val = obj
                        for attr in attr_chain:
                            val = getattr(val, attr, None) if val else None
                    
                    # Basic formatting
                    if isinstance(val, bool):
                        row.append("Ya" if val else "Tidak")
                    elif val is None:
                        row.append("-")
                    else:
                        row.append(val)
                ws.append(row)
                total_rows += 1
            
            offset += batch_size
            if len(batch) < batch_size:
                break

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        jakarta = pytz.timezone("Asia/Jakarta")
        timestamp = datetime.now(jakarta).strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
