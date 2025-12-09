"""Memory Optimization Utilities for Record Matcher.

This module provides memory-efficient data handling techniques including:
- Lazy loading for large datasets
- Generators for iterative processing
- Pagination for UI display
- Weak references for cache management
- Resource cleanup helpers
- Memory profiling utilities

Author: Record Matcher Development Team
Date: December 2025
"""

from typing import Dict, List, Any, Iterator, Optional, Callable, TypeVar, Generic
from collections.abc import Sequence
import weakref
import gc
import locale
from contextlib import contextmanager
from functools import wraps
import threading

T = TypeVar('T')


# ============================================================================
# LAZY LOADING
# ============================================================================

class LazyDataLoader(Generic[T]):
    """Lazy loader for large datasets - loads data only when accessed.
    
    This class implements the lazy loading pattern to defer expensive data
    loading operations until the data is actually needed. This is especially
    useful for large Excel files, database queries, or API calls.
    
    Example:
        >>> def load_excel():
        ...     return expensive_excel_read()
        >>> lazy_data = LazyDataLoader(load_excel)
        >>> # Data not loaded yet
        >>> data = lazy_data.get()  # Loads now
        >>> data2 = lazy_data.get()  # Returns cached data
    """
    
    def __init__(self, loader_func: Callable[[], T]):
        """Initialize lazy loader.
        
        Args:
            loader_func: Function that loads the data when called
        """
        self._loader_func = loader_func
        self._data: Optional[T] = None
        self._loaded = False
        self._lock = threading.Lock()
    
    def get(self) -> T:
        """Get data (load if not already loaded).
        
        Returns:
            The loaded data
        """
        if not self._loaded:
            with self._lock:
                # Double-check locking pattern
                if not self._loaded:
                    self._data = self._loader_func()
                    self._loaded = True
        return self._data
    
    def is_loaded(self) -> bool:
        """Check if data has been loaded.
        
        Returns:
            True if data is loaded, False otherwise
        """
        return self._loaded
    
    def clear(self):
        """Clear loaded data to free memory."""
        with self._lock:
            self._data = None
            self._loaded = False
            gc.collect()
    
    def reload(self) -> T:
        """Force reload of data.
        
        Returns:
            Freshly loaded data
        """
        self.clear()
        return self.get()


# ============================================================================
# GENERATORS FOR LARGE DATASETS
# ============================================================================

def batch_processor(items: Sequence[T], batch_size: int = 100) -> Iterator[List[T]]:
    """Process items in batches using generator (memory efficient).
    
    Instead of loading all items at once, yields batches for processing.
    This is much more memory efficient for large datasets.
    
    Example:
        >>> large_list = range(10000)
        >>> for batch in batch_processor(large_list, batch_size=100):
        ...     process_batch(batch)  # Only 100 items in memory
    
    Args:
        items: Sequence to process
        batch_size: Number of items per batch
    
    Yields:
        Batches of items
    """
    total = len(items)
    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        yield items[start_idx:end_idx]


def filter_generator(items: Sequence[T], predicate: Callable[[T], bool]) -> Iterator[T]:
    """Filter items using generator (memory efficient alternative to list comprehension).
    
    Example:
        >>> # Instead of: [item for item in large_list if condition(item)]
        >>> # Use: filter_generator(large_list, condition)
        >>> filtered = filter_generator(data, lambda x: x['amount'] > 1000)
        >>> for item in filtered:
        ...     process(item)
    
    Args:
        items: Items to filter
        predicate: Function that returns True for items to keep
    
    Yields:
        Items that match the predicate
    """
    for item in items:
        if predicate(item):
            yield item


def map_generator(items: Sequence[T], transform: Callable[[T], Any]) -> Iterator[Any]:
    """Transform items using generator (memory efficient alternative to list comprehension).
    
    Example:
        >>> # Instead of: [transform(item) for item in large_list]
        >>> # Use: map_generator(large_list, transform)
        >>> transformed = map_generator(data, lambda x: x['value'] * 2)
    
    Args:
        items: Items to transform
        transform: Function to apply to each item
    
    Yields:
        Transformed items
    """
    for item in items:
        yield transform(item)


def format_table_generator(table_data: List[Dict]) -> Iterator[Dict]:
    """Format table data using generator (avoids deepcopy memory overhead).
    
    This is a memory-efficient replacement for format_table_data() that
    uses deepcopy. Instead of copying the entire table, it yields formatted
    rows one at a time.
    
    Example:
        >>> formatted = list(format_table_generator(raw_data))
        >>> # Or iterate directly:
        >>> for row in format_table_generator(raw_data):
        ...     display(row)
    
    Args:
        table_data: Raw table data
    
    Yields:
        Formatted rows (Credit/Debit with locale formatting)
    """
    for row in table_data:
        # Create shallow copy of row and format numbers
        formatted_row = row.copy()
        
        if formatted_row.get('Credit') != '':
            try:
                formatted_row['Credit'] = locale.format_string(
                    "%.2f", float(formatted_row['Credit']), grouping=True
                )
            except (ValueError, TypeError):
                pass
        
        if formatted_row.get('Debit') != '':
            try:
                formatted_row['Debit'] = locale.format_string(
                    "%.2f", float(formatted_row['Debit']), grouping=True
                )
            except (ValueError, TypeError):
                pass
        
        if formatted_row.get('Closing Balance') != '':
            try:
                formatted_row['Closing Balance'] = locale.format_string(
                    "%.2f", float(formatted_row['Closing Balance']), grouping=True
                )
            except (ValueError, TypeError):
                pass
        
        yield formatted_row


# ============================================================================
# PAGINATION
# ============================================================================

class Paginator(Generic[T]):
    """Paginate large datasets for UI display (load only visible pages).
    
    Instead of loading all rows into UI, load only the current page.
    This dramatically improves performance and memory usage for large tables.
    
    Example:
        >>> data = [1, 2, 3, ..., 10000]  # Large dataset
        >>> paginator = Paginator(data, page_size=100)
        >>> page1 = paginator.get_page(1)  # Only 100 items
        >>> total_pages = paginator.total_pages  # 100
    """
    
    def __init__(self, items: Sequence[T], page_size: int = 100):
        """Initialize paginator.
        
        Args:
            items: All items to paginate
            page_size: Number of items per page
        """
        self._items = items
        self._page_size = page_size
        self._total_items = len(items)
        self._total_pages = (self._total_items + page_size - 1) // page_size
    
    @property
    def total_items(self) -> int:
        """Total number of items."""
        return self._total_items
    
    @property
    def total_pages(self) -> int:
        """Total number of pages."""
        return self._total_pages
    
    @property
    def page_size(self) -> int:
        """Items per page."""
        return self._page_size
    
    def get_page(self, page_number: int) -> List[T]:
        """Get specific page of data.
        
        Args:
            page_number: Page number (1-indexed)
        
        Returns:
            List of items for the requested page
        
        Raises:
            ValueError: If page number is invalid
        """
        if page_number < 1 or page_number > self._total_pages:
            raise ValueError(
                f"Invalid page number {page_number}. "
                f"Valid range: 1-{self._total_pages}"
            )
        
        start_idx = (page_number - 1) * self._page_size
        end_idx = min(start_idx + self._page_size, self._total_items)
        return self._items[start_idx:end_idx]
    
    def get_page_info(self, page_number: int) -> Dict[str, Any]:
        """Get page information (for UI display).
        
        Args:
            page_number: Page number (1-indexed)
        
        Returns:
            Dictionary with page metadata
        """
        start_idx = (page_number - 1) * self._page_size + 1
        end_idx = min(start_idx + self._page_size - 1, self._total_items)
        
        return {
            'page_number': page_number,
            'total_pages': self._total_pages,
            'page_size': self._page_size,
            'total_items': self._total_items,
            'start_index': start_idx,
            'end_index': end_idx,
            'showing': f"{start_idx}-{end_idx} of {self._total_items}",
            'has_previous': page_number > 1,
            'has_next': page_number < self._total_pages,
        }


# ============================================================================
# WEAK REFERENCES FOR CACHE MANAGEMENT
# ============================================================================

class WeakValueCache(Generic[T]):
    """Cache with weak references - automatically releases memory when needed.
    
    Unlike a regular cache that holds strong references (preventing garbage
    collection), this cache uses weak references. When memory is low, the
    garbage collector can automatically clean up cached items.
    
    Example:
        >>> cache = WeakValueCache()
        >>> expensive_object = load_large_dataframe()
        >>> cache.set('data', expensive_object)
        >>> # Object can be GC'd if no other references exist
        >>> data = cache.get('data')  # May return None if GC'd
    """
    
    def __init__(self):
        """Initialize weak value cache."""
        self._cache: Dict[str, weakref.ref] = {}
        self._lock = threading.Lock()
    
    def set(self, key: str, value: T) -> bool:
        """Set cache entry with weak reference.
        
        Args:
            key: Cache key
            value: Value to cache (must be an object, not a primitive)
        
        Returns:
            True if successfully cached, False if value cannot be weakly referenced
        """
        try:
            with self._lock:
                self._cache[key] = weakref.ref(value)
            return True
        except TypeError:
            # Cannot create weak reference to this type (e.g., int, str)
            return False
    
    def get(self, key: str) -> Optional[T]:
        """Get cached value.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if exists and not garbage collected, None otherwise
        """
        with self._lock:
            ref = self._cache.get(key)
            if ref is None:
                return None
            
            value = ref()  # Dereference
            if value is None:
                # Object was garbage collected, remove dead reference
                del self._cache[key]
            return value
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def cleanup(self):
        """Remove dead references from cache."""
        with self._lock:
            dead_keys = [key for key, ref in self._cache.items() if ref() is None]
            for key in dead_keys:
                del self._cache[key]
    
    def size(self) -> int:
        """Get number of cached items (including dead references)."""
        return len(self._cache)


# ============================================================================
# RESOURCE CLEANUP HELPERS
# ============================================================================

@contextmanager
def managed_excel_workbook(workbook):
    """Context manager for Excel workbook cleanup.
    
    Ensures workbook resources are always released, even on exceptions.
    
    Example:
        >>> wb = open_workbook('data.xlsx')
        >>> with managed_excel_workbook(wb):
        ...     sheet = wb.sheet_by_index(0)
        ...     process(sheet)
        >>> # Workbook automatically released
    
    Args:
        workbook: Excel workbook object
    
    Yields:
        The workbook object
    """
    try:
        yield workbook
    finally:
        if hasattr(workbook, 'release_resources'):
            try:
                workbook.release_resources()
            except:
                pass  # Ignore errors during cleanup


@contextmanager
def managed_resources(*resources):
    """Context manager for multiple resources with cleanup.
    
    Example:
        >>> wb1 = open_workbook('file1.xlsx')
        >>> wb2 = open_workbook('file2.xlsx')
        >>> with managed_resources(wb1, wb2):
        ...     process_both(wb1, wb2)
        >>> # Both workbooks released
    
    Args:
        *resources: Resources with release_resources() or close() methods
    
    Yields:
        Tuple of resources
    """
    try:
        yield resources
    finally:
        for resource in resources:
            if resource is None:
                continue
            
            # Try common cleanup methods
            for method_name in ['release_resources', 'close', '__exit__']:
                if hasattr(resource, method_name):
                    try:
                        method = getattr(resource, method_name)
                        if method_name == '__exit__':
                            method(None, None, None)
                        else:
                            method()
                        break
                    except:
                        pass


def clear_large_objects(*objects):
    """Explicitly delete large objects and trigger garbage collection.
    
    Use this after processing large datasets to immediately free memory
    instead of waiting for automatic garbage collection.
    
    Example:
        >>> large_df = process_huge_dataset()
        >>> results = extract_summary(large_df)
        >>> clear_large_objects(large_df)  # Free memory immediately
    
    Args:
        *objects: Objects to delete
    """
    for obj in objects:
        try:
            del obj
        except:
            pass
    
    # Force garbage collection
    gc.collect()


def memory_efficient_decorator(func: Callable) -> Callable:
    """Decorator to ensure cleanup after function execution.
    
    Automatically triggers garbage collection after function completes,
    ensuring memory is released promptly for memory-intensive operations.
    
    Example:
        >>> @memory_efficient_decorator
        ... def process_large_file(filename):
        ...     data = load_huge_file(filename)
        ...     return analyze(data)
        >>> # Memory freed automatically after function returns
    
    Args:
        func: Function to decorate
    
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            gc.collect()
    return wrapper


# ============================================================================
# EFFICIENT DATA COPYING ALTERNATIVES
# ============================================================================

def shallow_copy_with_format(row: Dict, format_fields: List[str]) -> Dict:
    """Create shallow copy and format only specified fields.
    
    More efficient than deepcopy when only a few fields need formatting.
    
    Example:
        >>> row = {'Credit': 1000.50, 'Debit': '', 'Name': 'John'}
        >>> formatted = shallow_copy_with_format(row, ['Credit', 'Debit'])
        >>> # Only Credit/Debit formatted, rest shared
    
    Args:
        row: Original row dictionary
        format_fields: Fields to format (create new objects for)
    
    Returns:
        Shallow copy with formatted fields
    """
    result = row.copy()  # Shallow copy
    
    for field in format_fields:
        if field in result and result[field] != '':
            try:
                value = float(result[field])
                result[field] = locale.format_string("%.2f", value, grouping=True)
            except (ValueError, TypeError):
                pass
    
    return result


def format_table_data_efficient(table_data: List[Dict]) -> List[Dict]:
    """Format table data without deepcopy (memory efficient).
    
    Replacement for the original format_table_data() that uses deepcopy.
    This version creates shallow copies and only formats number fields,
    reducing memory usage significantly.
    
    Args:
        table_data: Raw table data
    
    Returns:
        Formatted table data (shallow copies with formatted numbers)
    """
    format_fields = ['Credit', 'Debit', 'Closing Balance']
    return [shallow_copy_with_format(row, format_fields) for row in table_data]


# ============================================================================
# MEMORY PROFILING UTILITIES
# ============================================================================

def get_object_size(obj) -> int:
    """Get approximate size of object in bytes.
    
    Args:
        obj: Object to measure
    
    Returns:
        Size in bytes
    """
    import sys
    return sys.getsizeof(obj)


def log_memory_usage(label: str = ""):
    """Log current memory usage (for debugging).
    
    Args:
        label: Optional label for the log entry
    """
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"[Memory] {label}: {memory_mb:.2f} MB")


# ============================================================================
# EXAMPLE USAGE PATTERNS
# ============================================================================

if __name__ == "__main__":
    print("Memory Optimization Utilities - Example Usage\n")
    
    # Example 1: Lazy Loading
    print("1. Lazy Loading Example:")
    def expensive_load():
        print("   Loading expensive data...")
        return list(range(1000000))
    
    lazy = LazyDataLoader(expensive_load)
    print(f"   Loaded: {lazy.is_loaded()}")  # False
    data = lazy.get()  # Triggers load
    print(f"   Loaded: {lazy.is_loaded()}")  # True
    print(f"   Items: {len(data)}")
    lazy.clear()  # Free memory
    print()
    
    # Example 2: Generators vs List Comprehensions
    print("2. Generator Example:")
    large_data = list(range(10000))
    
    # Memory inefficient:
    # filtered = [x for x in large_data if x % 2 == 0]
    
    # Memory efficient:
    filtered_gen = filter_generator(large_data, lambda x: x % 2 == 0)
    print(f"   First 5 even numbers: {list(itertools.islice(filtered_gen, 5))}")
    print()
    
    # Example 3: Pagination
    print("3. Pagination Example:")
    table_data = [{'id': i, 'value': i * 10} for i in range(1000)]
    paginator = Paginator(table_data, page_size=10)
    
    page1 = paginator.get_page(1)
    info = paginator.get_page_info(1)
    print(f"   {info['showing']}")
    print(f"   Page 1 items: {len(page1)}")
    print()
    
    # Example 4: Weak Reference Cache
    print("4. Weak Reference Cache Example:")
    cache = WeakValueCache()
    
    class LargeObject:
        def __init__(self, size):
            self.data = [0] * size
    
    obj = LargeObject(1000)
    cache.set('large', obj)
    print(f"   Cached: {cache.get('large') is not None}")
    
    del obj  # Remove strong reference
    gc.collect()
    print(f"   After GC: {cache.get('large') is not None}")
    print()
    
    # Example 5: Resource Management
    print("5. Resource Management Example:")
    class FakeWorkbook:
        def __init__(self, name):
            self.name = name
            print(f"   Opened: {name}")
        
        def release_resources(self):
            print(f"   Released: {self.name}")
    
    with managed_resources(FakeWorkbook("file1"), FakeWorkbook("file2")):
        print("   Processing files...")
    print("   Done (resources auto-released)")
    
    import itertools
