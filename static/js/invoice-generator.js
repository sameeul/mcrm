function generateInvoicePDF(orderData) {
    const { jsPDF } = window.jspdf;
    
    // Custom page size: 100mm x 70mm (converted to points: 1mm = 2.834645669 points)
    const pageWidth = 100 * 2.834645669;  // 283.46 points
    const pageHeight = 70 * 2.834645669;  // 198.43 points
    
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: [pageWidth, pageHeight]
    });
    
    // PDF Configuration
    const margin = 8; // 3mm margins
    let yPosition = margin;
    const contentWidth = pageWidth - 2 * margin;
    
    // Helper function to add text with automatic line wrapping
    function addText(text, x, y, options = {}) {
        const fontSize = options.fontSize || 6;
        const maxWidth = options.maxWidth || contentWidth;
        const align = options.align || 'left';
        const lineHeight = options.lineHeight || fontSize * 1.2;
        
        doc.setFontSize(fontSize);
        
        if (options.bold) {
            doc.setFont(undefined, 'bold');
        } else {
            doc.setFont(undefined, 'normal');
        }
        
        const lines = doc.splitTextToSize(text, maxWidth);
        
        for (let i = 0; i < lines.length; i++) {
            let xPos = x;
            if (align === 'center') {
                xPos = pageWidth / 2;
            } else if (align === 'right') {
                xPos = pageWidth - margin;
            }
            
            doc.text(lines[i], xPos, y + (i * lineHeight), { align: align });
        }
        
        return y + (lines.length * lineHeight);
    }
    
    // Helper function to check if we need a new page
    function checkNewPage(requiredHeight) {
        if (yPosition + requiredHeight > pageHeight - margin) {
            doc.addPage();
            yPosition = margin;
            return true;
        }
        return false;
    }
    
    // Helper function to draw a horizontal line
    function drawLine(y, width = contentWidth) {
        doc.setDrawColor(0, 0, 0);
        doc.line(margin, y, margin + width, y);
        return y + 3;
    }
    
    // Company Header
    yPosition = addText('MURDHANNO', pageWidth / 2, yPosition + 8, {
        fontSize: 8,
        bold: true,
        align: 'center'
    });
    
    yPosition += 2;
    
    // Invoice Title and Date
    const headerText = `Invoice #${orderData.id} | ${orderData.date}`;
    yPosition = addText(headerText, pageWidth / 2, yPosition, {
        fontSize: 6,
        align: 'center'
    });
    
    yPosition += 3;
    yPosition = drawLine(yPosition);
    
    // Customer Information
    yPosition = addText(`Customer: ${orderData.customer.name}`, margin, yPosition, {
        fontSize: 6,
        maxWidth: contentWidth
    });
    
    yPosition += 1;
    yPosition = addText(`Phone: ${orderData.customer.phone}`, margin, yPosition, {
        fontSize: 6
    });
    
    yPosition += 1;
    yPosition = addText(`Address: ${orderData.customer.address}`, margin, yPosition, {
        fontSize: 6,
        maxWidth: contentWidth
    });
    
    yPosition += 3;
    yPosition = drawLine(yPosition);
    
    // Items Table Header
    const colWidths = [56, 127, 42, 56]; // SKU, Product, Qty, Price (in points)
    const colPositions = [margin];
    
    for (let i = 1; i < colWidths.length; i++) {
        colPositions.push(colPositions[i-1] + colWidths[i-1]);
    }
    
    // Check if we need a new page for the table
    checkNewPage(20);
    
    // Table headers
    doc.setFontSize(6);
    doc.setFont(undefined, 'bold');
    doc.text('SKU', colPositions[0], yPosition);
    doc.text('Product', colPositions[1], yPosition);
    doc.text('Qty', colPositions[2], yPosition);
    doc.text('Price', colPositions[3], yPosition);
    
    yPosition += 2;
    yPosition = drawLine(yPosition, contentWidth);
    
    // Table rows
    doc.setFont(undefined, 'normal');
    doc.setFontSize(6);
    
    orderData.items.forEach((item, index) => {
        // Check if we need a new page for this item
        checkNewPage(15);
        
        const startY = yPosition;
        
        // SKU
        doc.text(item.trackingCode, colPositions[0], yPosition);
        
        // Product Name + Size (with wrapping)
        const productText = `${item.productName} (Size: ${item.productSize})`;
        const productLines = doc.splitTextToSize(productText, colWidths[1] - 4);
        
        let maxLines = 1;
        for (let i = 0; i < productLines.length; i++) {
            doc.text(productLines[i], colPositions[1], yPosition + (i * 7));
            maxLines = Math.max(maxLines, i + 1);
        }
        
        // Quantity
        doc.text(item.quantity.toString(), colPositions[2], yPosition);
        
        // Price
        doc.text(`৳${item.unitPrice.toFixed(0)}`, colPositions[3], yPosition);
        
        // Move to next row (accounting for wrapped text)
        yPosition += maxLines * 7 + 2;
    });
    
    yPosition += 1;
    yPosition = drawLine(yPosition);
    
    // Summary Section
    checkNewPage(25);
    
    const summaryX = pageWidth - margin - 60;
    
    yPosition = addText(`Subtotal:`, summaryX - 40, yPosition, {
        fontSize: 6
    });
    yPosition = addText(`৳${orderData.subtotal.toFixed(0)}`, summaryX, yPosition - 7, {
        fontSize: 6,
        align: 'right'
    });
    
    if (orderData.deliveryCharge > 0) {
        yPosition = addText(`Delivery:`, summaryX - 40, yPosition + 1, {
            fontSize: 6
        });
        yPosition = addText(`৳${orderData.deliveryCharge.toFixed(0)}`, summaryX, yPosition - 7, {
            fontSize: 6,
            align: 'right'
        });
    }
    
    if (orderData.discount > 0) {
        yPosition = addText(`Discount:`, summaryX - 40, yPosition + 1, {
            fontSize: 6
        });
        yPosition = addText(`-৳${orderData.discount.toFixed(0)}`, summaryX, yPosition - 7, {
            fontSize: 6,
            align: 'right'
        });
    }
    
    // Draw line above total
    yPosition += 2;
    doc.setDrawColor(0, 0, 0);
    doc.line(summaryX - 40, yPosition, summaryX, yPosition);
    yPosition += 3;
    
    // Total
    yPosition = addText(`TOTAL:`, summaryX - 40, yPosition, {
        fontSize: 7,
        bold: true
    });
    yPosition = addText(`৳${orderData.total.toFixed(0)}`, summaryX, yPosition - 8, {
        fontSize: 7,
        bold: true,
        align: 'right'
    });
    
    yPosition += 3;
    yPosition = drawLine(yPosition);
    
    // Footer
    checkNewPage(10);
    yPosition = addText('Thank you!', pageWidth / 2, yPosition + 2, {
        fontSize: 6,
        align: 'center'
    });
    
    // Open PDF in new tab
    doc.output('dataurlnewwindow');
}
