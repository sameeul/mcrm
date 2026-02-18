function generateInvoicePDF(orderData) {
    const { jsPDF } = window.jspdf;

    const pageWidth = 288;  // 4 inches * 72 pts/inch
    const pageHeight = 432; // 6 inches * 72 pts/inch

    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: [pageWidth, pageHeight]
    });

    const margin = 16;
    let yPosition = margin;
    const contentWidth = pageWidth - 2 * margin;

    function addText(text, x, y, options = {}) {
        const fontSize = options.fontSize || 8;
        const maxWidth = options.maxWidth || contentWidth;
        const align = options.align || 'left';
        const lineHeight = options.lineHeight || fontSize * 1.4;

        doc.setFontSize(fontSize);
        doc.setFont(undefined, options.bold ? 'bold' : 'normal');

        const lines = doc.splitTextToSize(text, maxWidth);
        lines.forEach((line, i) => {
            let xPos = x;
            if (align === 'center') xPos = pageWidth / 2;
            else if (align === 'right') xPos = pageWidth - margin;

            doc.text(line, xPos, y + i * lineHeight, { align });
        });

        return y + lines.length * lineHeight;
    }

    function checkNewPage(requiredHeight) {
        if (yPosition + requiredHeight > pageHeight - margin) {
            doc.addPage();
            yPosition = margin;
            return true;
        }
        return false;
    }

    // Title
    yPosition = addText('MURDHANNO', pageWidth / 2, yPosition, {
        fontSize: 12, bold: true, align: 'center'
    });

    const paddedId = orderData.id.toString().padStart(5, '0');

    // Left-aligned invoice ID
    addText(`Invoice #${paddedId}`, margin, yPosition + 4, {
        fontSize: 8,
        align: 'left'
    });

    // Right-aligned date
    yPosition = addText(orderData.date, pageWidth - margin, yPosition + 4, {
        fontSize: 8,
        align: 'right'
});

    yPosition += 8;

    // Customer Info
    yPosition = addText(`Customer: ${orderData.customer.name}`, margin, yPosition, { fontSize: 8 });
    yPosition = addText(`Phone: ${orderData.customer.phone}`, margin, yPosition, { fontSize: 8 });
    yPosition = addText(`Address: ${orderData.customer.address}`, margin, yPosition, {
        fontSize: 8, maxWidth: contentWidth
    });

    yPosition += 10;

    // Column widths
    const colWidths = {
        description: 120,
        qty: 32,
        unitPrice: 44,
        total: 56
    };

    const colPositions = {
        description: margin,
        qty: margin + colWidths.description,
        unitPrice: margin + colWidths.description + colWidths.qty,
        total: pageWidth - margin - colWidths.total
    };

    // Table Headers
    checkNewPage(20);
    doc.setFontSize(8);
    doc.setFont(undefined, 'bold');
    doc.text('Description', colPositions.description, yPosition);
    doc.text('Qty', colPositions.qty + colWidths.qty - 2, yPosition, { align: 'right' });
    doc.text('Unit Price', colPositions.unitPrice + colWidths.unitPrice - 2, yPosition, { align: 'right' });
    doc.text('Total', colPositions.total + colWidths.total - 2, yPosition, { align: 'right' });

    yPosition += 12;
    doc.setFont(undefined, 'normal');

    // Table Rows
    orderData.items.forEach(item => {
        checkNewPage(24);

        const descriptionLines = doc.splitTextToSize(
            `${item.productName} - Size: ${item.productSize}`,
            colWidths.description - 4
        );

        // Description block
        descriptionLines.forEach((line, i) => {
            doc.text(line, colPositions.description, yPosition + i * 10);
        });

        const topY = yPosition;

        doc.text(item.quantity.toString(), colPositions.qty + colWidths.qty - 2, topY, { align: 'right' });
        doc.text(`Tk ${item.unitPrice.toFixed(0)}`, colPositions.unitPrice + colWidths.unitPrice - 2, topY, { align: 'right' });
        doc.text(`Tk ${(item.unitPrice * item.quantity).toFixed(0)}`, colPositions.total + colWidths.total - 2, topY, { align: 'right' });

        yPosition += descriptionLines.length * 10 + 4;
    });

    yPosition += 8;

    // Summary
    const summaryX = pageWidth - margin;
    const summaryLabelX = summaryX - 80;

    function addSummary(label, value) {
        yPosition = addText(label, summaryLabelX, yPosition, { fontSize: 8 });
        yPosition = addText(value, summaryX, yPosition - 12, { fontSize: 8, align: 'right' });
    }

    addSummary('Subtotal:', `Tk ${orderData.subtotal.toFixed(0)}`);
    if (orderData.deliveryCharge > 0)
        addSummary('Delivery:', `Tk ${orderData.deliveryCharge.toFixed(0)}`);
    if (orderData.discount > 0)
        addSummary('Discount:', `-Tk ${orderData.discount.toFixed(0)}`);

    yPosition += 8;

    yPosition = addText('TOTAL:', summaryLabelX, yPosition, { fontSize: 8, bold: true });
    yPosition = addText(`Tk ${orderData.total.toFixed(0)}`, summaryX, yPosition - 12, {
        fontSize: 8, bold: true, align: 'right'
    });

    yPosition += 12;

    yPosition = addText('Thank you!', pageWidth / 2, yPosition + 6, {
        fontSize: 8, align: 'center'
    });

    doc.output('dataurlnewwindow');
}
